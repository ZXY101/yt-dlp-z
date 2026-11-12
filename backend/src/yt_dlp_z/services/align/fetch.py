"""Gets one link's audio for alignment: yt-dlp downloads the smallest audio-only format to a
pipe, and ffmpeg turns it into raw PCM at the matcher's rate as it arrives. Converting while
downloading saves the separate convert step, and the download itself never touches disk."""

import asyncio
import contextlib
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.services.align.envelope import SAMPLE_RATE
from yt_dlp_z.services.jobs.process import ProcessHooks, ProcessResult, run_ytdlp
from yt_dlp_z.services.ytdlp.command import PROGRESS_MARKER
from yt_dlp_z.services.ytdlp.global_args import global_args
from yt_dlp_z.services.ytdlp.output import PERCENT, ProgressUpdate, Update

MAX_SECONDS = 12 * 3600
# Live streams would never finish downloading, and very long videos cost too much.
MATCH_FILTER = f"!is_live & duration <= {MAX_SECONDS}"
NOT_PASSING_HINT = "does not pass filter"
# yt-dlp's error when ffmpeg stopped reading (ffmpeg's own error says why).
BROKEN_PIPE_HINT = "Broken pipe"
# YouTube now and then refuses a fresh audio link; a new run of yt-dlp gets new links.
REFUSED_HINT = "HTTP Error 403"
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
    # The download is done and ffmpeg finishes converting what's left.
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
        "--no-quiet",
        *global_args(),
        *cookies,
        # To stdout, which is ffmpeg's input.
        "--output",
        "-",
        "--",
        request.url,
    ]


def decode_command(ffmpeg: list[str], target: Path) -> list[str]:
    return [
        *ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        "pipe:0",
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


@dataclass
class _Pipe:
    """The parent's ends of the pipe from yt-dlp to ffmpeg. Each end is closed once its child
    has it, so ffmpeg sees the end of the input when yt-dlp exits."""

    read: int | None
    write: int | None

    @classmethod
    def open(cls) -> "_Pipe":
        read, write = os.pipe()
        return cls(read, write)

    def close_read(self) -> None:
        if self.read is not None:
            os.close(self.read)
            self.read = None

    def close_write(self) -> None:
        if self.write is not None:
            os.close(self.write)
            self.write = None


class _DecodeError(Exception):
    """ffmpeg failed; the message is its error output."""

    def reason(self) -> str:
        lines = str(self).strip().splitlines()
        return f"ffmpeg couldn't read the audio: {lines[-1] if lines else 'failed'}"


async def _start_decoder(ffmpeg: list[str], pipe: _Pipe, target: Path) -> asyncio.Task[None]:
    """Starts ffmpeg on the pipe; the task ends when ffmpeg does."""
    try:
        process = await asyncio.create_subprocess_exec(
            *decode_command(ffmpeg, target),
            stdin=pipe.read,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
    finally:
        pipe.close_read()

    async def finish() -> None:
        try:
            _, stderr = await process.communicate()
        except asyncio.CancelledError:
            with contextlib.suppress(ProcessLookupError):
                process.kill()
            await process.wait()
            raise
        if process.returncode != 0:
            raise _DecodeError(stderr.decode(errors="replace"))

    return asyncio.create_task(finish())


async def _download(
    ytdlp: list[str], request: FetchRequest, pipe: _Pipe, hooks: FetchHooks
) -> tuple[ProcessResult, Path]:
    async def on_update(update: Update) -> None:
        if isinstance(update, ProgressUpdate) and update.progress is not None:
            await hooks.on_progress(update.progress / PERCENT)

    log = request.workdir / f"{request.name}.log"
    started = ProcessHooks(on_update=on_update, on_start=lambda _process: pipe.close_write())
    try:
        result = await run_ytdlp(download_command(ytdlp, request), log, started, pipe.write)
    finally:
        pipe.close_write()
    return result, log


def _download_error(result: ProcessResult, log: Path) -> str | None:
    """Why yt-dlp sent no usable audio, or None if it did its part."""
    if result.returncode != 0:
        return result.error or "yt-dlp couldn't download the audio"
    if NOT_PASSING_HINT in log.read_text(encoding="utf-8", errors="replace"):
        return f"Only ended streams and videos up to {MAX_SECONDS // 3600} hours can be aligned"
    return None


async def _finish(decoder: asyncio.Task[None], download_error: str | None) -> None:
    """Waits for ffmpeg; reports yt-dlp's error first, unless ffmpeg stopped reading first."""
    try:
        await decoder
    except _DecodeError as error:
        if download_error is None or BROKEN_PIPE_HINT in download_error:
            raise FetchError(error.reason()) from None
    if download_error is not None:
        raise FetchError(download_error)


async def fetch_audio(tools: Tools, request: FetchRequest, hooks: FetchHooks) -> Path:
    """Returns the PCM file, trying once more if YouTube refused the link. Cancelling stops
    both yt-dlp and ffmpeg."""
    try:
        return await _fetch_once(tools, request, hooks)
    except FetchError as error:
        if REFUSED_HINT not in str(error):
            raise
    return await _fetch_once(tools, request, hooks)


async def _fetch_once(tools: Tools, request: FetchRequest, hooks: FetchHooks) -> Path:
    target = request.workdir / f"{request.name}.pcm"
    pipe = _Pipe.open()
    try:
        decoder = await _start_decoder(tools.ffmpeg, pipe, target)
    except BaseException:
        pipe.close_write()
        raise
    try:
        result, log = await _download(tools.ytdlp, request, pipe, hooks)
        hooks.on_converting()
        await _finish(decoder, _download_error(result, log))
    except BaseException:
        decoder.cancel()
        with contextlib.suppress(asyncio.CancelledError, _DecodeError):
            await decoder
        raise
    if not target.exists() or target.stat().st_size == 0:
        raise FetchError("yt-dlp didn't send any audio")
    return target
