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


async def run_ytdlp(command: list[str], log_path: Path, hooks: ProcessHooks) -> ProcessResult:
    """Runs yt-dlp, streaming marker lines to on_update and everything else to the log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        # Own process group, so stopping it also stops ffmpeg and other children.
        start_new_session=True,
    )
    hooks.on_start(process)
    try:
        last_error = await _stream_output(process, log_path, hooks.on_update)
    except asyncio.CancelledError:
        # The app is shutting down. yt-dlp runs in its own session, so without this
        # it would keep downloading after the app exits.
        await stop_process(process, graceful=hooks.graceful)
        raise
    returncode = await process.wait()
    return ProcessResult(returncode=returncode, error=last_error)


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


async def _stream_output(
    process: asyncio.subprocess.Process,
    log_path: Path,
    on_update: Callable[[Update], Awaitable[None]],
) -> str | None:
    """Sends marker lines to on_update, logs everything else; returns the last error line."""
    last_error = None
    stdout = process.stdout
    if stdout is None:  # pragma: no cover  (always set with stdout=PIPE)
        raise RuntimeError("yt-dlp output is not available")
    with log_path.open("a", encoding="utf-8") as log:
        async for raw_line in _lines(stdout):
            line = raw_line.decode(errors="replace")
            update = parse_line(line)
            if update is not None:
                await on_update(update)
                continue
            log.write(line + "\n")
            log.flush()
            last_error = error_message(line) or last_error
    return last_error


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
