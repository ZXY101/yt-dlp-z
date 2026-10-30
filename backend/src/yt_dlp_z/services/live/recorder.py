"""Records a live stream, optionally as several files ("parts") of a set length.

yt-dlp can't split a recording itself, so each part is its own yt-dlp run: when a part's
time is up, yt-dlp gets SIGINT (it then finishes and merges the file, like Ctrl+C) and the
next part starts, recording from now. There can be a gap of a few seconds between parts.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from yt_dlp_z.db.models.job import Job, JobStatus
from yt_dlp_z.services.jobs.process import ProcessResult, interrupt_process

# yt-dlp's own default file name.
DEFAULT_OUTPUT = "%(title)s [%(id)s].%(ext)s"
EXT_SUFFIX = ".%(ext)s"
# Waits (retrying every 30 s to 5 min) when the stream starts later than announced.
WAIT_ARGS = ["--wait-for-video", "30-300"]

Outcome = tuple[JobStatus, str | None]
RunPart = Callable[
    [list[str], Callable[[asyncio.subprocess.Process], None]], Awaitable[ProcessResult]
]


def part_template(template: str | None, part: int) -> str:
    """The file name template with " (part N)" before the extension."""
    base = template or DEFAULT_OUTPUT
    if base.endswith(EXT_SUFFIX):
        return f"{base.removesuffix(EXT_SUFFIX)} (part {part}){EXT_SUFFIX}"
    return f"{base} (part {part})"


def part_args(job: Job, part: int) -> list[str]:
    """Only the first part records from the stream's start; later ones continue from now."""
    args = list(WAIT_ARGS)
    if part == 1 and job.record_from_start:
        args = ["--live-from-start", *args]
    # Numbered files when splitting, and after a restart (part > 1), so a continued
    # recording never collides with the file already saved.
    if job.part_seconds or part > 1:
        template = job.options.get("--output")
        args += ["--output", part_template(template if isinstance(template, str) else None, part)]
    return args


@dataclass
class PartTimer:
    """Stops the running part when its time is up."""

    seconds: float | None
    timed_out: bool = False
    _handle: asyncio.TimerHandle | None = None

    def start(self, process: asyncio.subprocess.Process) -> None:
        if self.seconds is not None:
            self._handle = asyncio.get_running_loop().call_later(self.seconds, self._stop, process)

    def _stop(self, process: asyncio.subprocess.Process) -> None:
        self.timed_out = True
        interrupt_process(process)

    def cancel(self) -> None:
        if self._handle is not None:
            self._handle.cancel()


def part_length(job: Job, elapsed: float) -> float | None:
    """How long the next part may run: its own length, capped by what max_seconds leaves."""
    lengths: list[float] = [job.part_seconds] if job.part_seconds else []
    if job.max_seconds:
        lengths.append(max(0.0, job.max_seconds - elapsed))
    return min(lengths) if lengths else None


def _part_outcome(result: ProcessResult, cancelled: bool) -> Outcome:
    if cancelled:
        return JobStatus.CANCELLED, None
    if result.returncode == 0:
        return JobStatus.COMPLETED, None
    return JobStatus.FAILED, result.error or f"yt-dlp exited with code {result.returncode}."


@dataclass(frozen=True)
class RecordingHooks:
    run_part: RunPart
    on_start: Callable[[asyncio.subprocess.Process], None]
    is_cancelled: Callable[[], bool]
    # Saves the job (its part number) before each part starts.
    on_part: Callable[[int], Awaitable[None]]


async def record(job: Job, hooks: RecordingHooks) -> Outcome:
    started = time.monotonic()
    # After a restart the recording continues with the next part.
    part = (job.part or 0) + 1
    while True:
        await hooks.on_part(part)
        timer = PartTimer(part_length(job, time.monotonic() - started))

        def on_start(process: asyncio.subprocess.Process, timer: PartTimer = timer) -> None:
            hooks.on_start(process)
            timer.start(process)

        try:
            result = await hooks.run_part(part_args(job, part), on_start)
        finally:
            timer.cancel()
        # A part stopped by its timer ends normally; anything else ends the recording.
        if hooks.is_cancelled() or not timer.timed_out:
            return _part_outcome(result, hooks.is_cancelled())
        if job.max_seconds and time.monotonic() - started >= job.max_seconds:
            return JobStatus.COMPLETED, None
        part += 1
