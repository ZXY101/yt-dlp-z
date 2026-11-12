import asyncio
import contextlib
import os
import re
import signal
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.services.ytdlp.output import Update, error_message, parse_line

KILL_AFTER_SECONDS = 5
READ_CHUNK_BYTES = 65_536
# ffmpeg ends its progress updates with \r only; they count as lines too.
LINE_END = re.compile(rb"\r\n|\r|\n")
# yt-dlp's warning when it can't renew a live stream's expired links ("Cannot find
# refreshed url for format 303"); after three tries it stops and saves what it has.
EXPIRED_LINKS_HINT = "Cannot find refreshed url"
# A recording stopped with SIGINT merges what it has; for hours of video that takes a while.
GRACEFUL_STOP_SECONDS = 600


@dataclass(frozen=True)
class ProcessHooks:
    on_update: Callable[[Update], Awaitable[None]]
    on_start: Callable[[asyncio.subprocess.Process], None]
    # On shutdown, let yt-dlp finish its file first (recordings).
    graceful: bool = False


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    error: str | None
    # yt-dlp couldn't renew a live stream's expired links (YouTube's expire after about
    # 6 h) and stopped recording, although the stream may still be live.
    links_expired: bool = False


async def run_ytdlp(
    command: list[str], log_path: Path, hooks: ProcessHooks, media: int | None = None
) -> ProcessResult:
    """Runs yt-dlp, streaming marker lines to on_update and everything else to the log.

    `media`: a file descriptor for the download itself (`--output -`). yt-dlp then writes its
    messages to stderr, so they're read from there."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE if media is None else media,
        stderr=asyncio.subprocess.STDOUT if media is None else asyncio.subprocess.PIPE,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        # Own process group, so stopping it also stops ffmpeg and other children.
        start_new_session=True,
    )
    hooks.on_start(process)
    try:
        output = await _stream_output(process, log_path, hooks.on_update)
    except asyncio.CancelledError:
        # The app is shutting down. yt-dlp runs in its own session, so without this
        # it would keep downloading after the app exits.
        await stop_process(process, graceful=hooks.graceful)
        raise
    returncode = await process.wait()
    return ProcessResult(returncode, output.last_error, output.links_expired)


async def _lines(stdout: asyncio.StreamReader) -> AsyncIterator[bytes]:
    """Output lines, ended by \n, \r\n or a lone \r."""
    pending = b""
    while chunk := await stdout.read(READ_CHUNK_BYTES):
        *lines, pending = LINE_END.split(pending + chunk)
        for line in lines:
            if line:
                yield line
    if pending:
        yield pending


@dataclass
class _Output:
    last_error: str | None = None
    links_expired: bool = False


async def _stream_output(
    process: asyncio.subprocess.Process,
    log_path: Path,
    on_update: Callable[[Update], Awaitable[None]],
) -> _Output:
    """Sends marker lines to on_update, logs everything else; returns what the log showed."""
    output = _Output()
    # Messages come on stdout, or on stderr while stdout carries the download.
    messages = process.stdout or process.stderr
    if messages is None:  # pragma: no cover  (one of them is always a pipe)
        raise RuntimeError("yt-dlp output is not available")
    with log_path.open("a", encoding="utf-8") as log:
        async for raw_line in _lines(messages):
            line = raw_line.decode(errors="replace")
            update = parse_line(line)
            if update is not None:
                await on_update(update)
                continue
            log.write(line + "\n")
            log.flush()
            output.last_error = error_message(line) or output.last_error
            if EXPIRED_LINKS_HINT in line:
                output.links_expired = True
    return output


def interrupt_process(process: asyncio.subprocess.Process) -> None:
    """SIGINT to yt-dlp and its children (ffmpeg): like Ctrl+C, they finish the file."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGINT)


async def stop_process(process: asyncio.subprocess.Process, graceful: bool = False) -> None:
    """SIGTERM the process group, then SIGKILL it if it hasn't exited in time.
    `graceful` first asks with SIGINT, so a recording keeps what it has recorded."""
    if graceful:
        interrupt_process(process)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(process.wait(), GRACEFUL_STOP_SECONDS)
            return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        await asyncio.wait_for(process.wait(), KILL_AFTER_SECONDS)
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        await process.wait()
