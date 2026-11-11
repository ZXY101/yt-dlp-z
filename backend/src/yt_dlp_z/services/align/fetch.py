"""Gets one link's audio for alignment: the smallest audio-only format through yt-dlp,
then ffmpeg turns it into raw PCM at the matcher's rate and the download is deleted."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.services.align.envelope import SAMPLE_RATE
from yt_dlp_z.services.jobs.process import ProcessHooks, run_ytdlp
from yt_dlp_z.services.ytdlp.command import FILE_MARKER, PROGRESS_MARKER
from yt_dlp_z.services.ytdlp.global_args import global_args
from yt_dlp_z.services.ytdlp.output import PERCENT, FileUpdate, ProgressUpdate, Update

MAX_SECONDS = 12 * 3600
# Live streams would never finish downloading, and very long videos cost too much.
MATCH_FILTER = f"!is_live & duration <= {MAX_SECONDS}"
NOT_PASSING_HINT = "does not pass filter"
# The smallest audio-only format over plain HTTPS. On YouTube, plain "worstaudio" can pick an
# HLS (m3u8) stream fetched in many small pieces: about 3x slower for the same size.
AUDIO_FORMAT = "worstaudio[protocol=https]/worstaudio/worst"


class FetchError(Exception):
    pass


@dataclass(frozen=True)
class FetchRequest:
    url: str
    workdir: Path
    name: str
    cookies: Path | None = None


@dataclass(frozen=True)
class FetchHooks:
    on_progress: Callable[[float], Awaitable[None]]
    # The download is done and ffmpeg starts converting it.
    on_converting: Callable[[], None]


@dataclass(frozen=True)
class Tools:
    ytdlp: list[str]
    ffmpeg: list[str]


def download_command(ytdlp: list[str], request: FetchRequest) -> list[str]:
    cookies = ["--cookies", str(request.cookies)] if request.cookies else []
    return [
        *ytdlp,
        "--ignore-config",
        "--newline",
        "--color",
        "never",
        "--no-playlist",
        "--format",
        AUDIO_FORMAT,
        "--match-filter",
        MATCH_FILTER,
        "--progress",
        "--progress-template",
        f"download:{PROGRESS_MARKER}%(progress)j",
        "--print",
        f"after_move:{FILE_MARKER}%(filepath)j",
        "--no-quiet",
        *global_args(),
        *cookies,
        "--paths",
        f"home:{request.workdir}",
        "--output",
        f"{request.name}.%(ext)s",
        "--",
        request.url,
    ]


def decode_command(ffmpeg: list[str], source: Path, target: Path) -> list[str]:
    return [
        *ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-t",
        str(MAX_SECONDS),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "s16le",
        "-acodec",
        "pcm_s16le",
        str(target),
    ]


async def _download(
    ytdlp: list[str], request: FetchRequest, on_progress: Callable[[float], Awaitable[None]]
) -> Path:
    files: list[str] = []

    async def on_update(update: Update) -> None:
        if isinstance(update, FileUpdate):
            files.append(update.filepath)
        elif isinstance(update, ProgressUpdate) and update.progress is not None:
            await on_progress(update.progress / PERCENT)

    log = request.workdir / f"{request.name}.log"
    hooks = ProcessHooks(on_update=on_update, on_start=lambda _process: None)
    result = await run_ytdlp(download_command(ytdlp, request), log, hooks)
    if result.returncode != 0:
        raise FetchError(result.error or "yt-dlp couldn't download the audio")
    if not files:
        raise FetchError(_no_file_reason(log))
    path = Path(files[-1])
    # It's deleted after decoding, so it must be the file this run created.
    if path.parent != request.workdir:
        raise FetchError("yt-dlp saved the audio somewhere unexpected")
    return path


def _no_file_reason(log: Path) -> str:
    if NOT_PASSING_HINT in log.read_text(encoding="utf-8", errors="replace"):
        return f"Only ended streams and videos up to {MAX_SECONDS // 3600} hours can be aligned"
    return "yt-dlp didn't save any audio"


async def _decode(ffmpeg: list[str], source: Path, target: Path) -> None:
    process = await asyncio.create_subprocess_exec(
        *decode_command(ffmpeg, source, target),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await process.communicate()
    except asyncio.CancelledError:
        process.kill()
        await process.wait()
        raise
    if process.returncode != 0:
        detail = stderr.decode(errors="replace").strip().splitlines()
        raise FetchError(f"ffmpeg couldn't read the audio: {detail[-1] if detail else 'failed'}")


async def fetch_audio(tools: Tools, request: FetchRequest, hooks: FetchHooks) -> Path:
    """Returns the PCM file. The downloaded file is gone afterwards, even on errors."""
    downloaded = await _download(tools.ytdlp, request, hooks.on_progress)
    hooks.on_converting()
    target = request.workdir / f"{request.name}.pcm"
    try:
        await _decode(tools.ffmpeg, downloaded, target)
    finally:
        downloaded.unlink(missing_ok=True)
    return target
