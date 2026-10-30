import asyncio
import contextlib
import os
import signal
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.services.ytdlp.output import Update, error_message, parse_line

KILL_AFTER_SECONDS = 5


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    error: str | None


async def run_ytdlp(
    command: list[str],
    log_path: Path,
    on_update: Callable[[Update], Awaitable[None]],
    on_start: Callable[[asyncio.subprocess.Process], None],
) -> ProcessResult:
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
    on_start(process)
    try:
        last_error = await _stream_output(process, log_path, on_update)
    except asyncio.CancelledError:
        # The app is shutting down. yt-dlp runs in its own session, so without this
        # it would keep downloading after the app exits.
        await stop_process(process)
        raise
    returncode = await process.wait()
    return ProcessResult(returncode=returncode, error=last_error)


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
        async for raw_line in stdout:
            line = raw_line.decode(errors="replace").rstrip("\r\n")
            update = parse_line(line)
            if update is not None:
                await on_update(update)
                continue
            log.write(line + "\n")
            log.flush()
            last_error = error_message(line) or last_error
    return last_error


async def stop_process(process: asyncio.subprocess.Process) -> None:
    """SIGTERM the process group, then SIGKILL it if it hasn't exited in time."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        await asyncio.wait_for(process.wait(), KILL_AFTER_SECONDS)
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        await process.wait()
