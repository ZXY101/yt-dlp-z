"""Records a live stream, optionally as several files ("parts") of a set length.

yt-dlp can't split a recording itself, so each part is its own yt-dlp run: when a part's
time is up, yt-dlp gets SIGINT (it then finishes and merges the file, like Ctrl+C) and the
next part starts, recording from now. There can be a gap of a few seconds between parts.
A maximum length counts hours of the stream saved (see StreamClock), not hours spent.

YouTube's stream links expire after about 6 hours. yt-dlp should renew them, but often
can't ("Cannot find refreshed url"); it then stops and saves the file as if the stream
had ended. When the stream is still live, the recording continues with the next part.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.db.models.job import Job, JobStatus
from yt_dlp_z.services.jobs.process import ProcessResult, interrupt_process
from yt_dlp_z.services.live.stream_clock import StreamClock, as_utc
from yt_dlp_z.services.media_server.layout import output_template
from yt_dlp_z.services.ytdlp.output import ProgressUpdate

# yt-dlp's own default file name.
DEFAULT_OUTPUT = "%(title)s [%(id)s].%(ext)s"
EXT_SUFFIX = ".%(ext)s"
# Waits (retrying every 30 s to 5 min) when the stream starts later than announced.
WAIT_ARGS = ["--wait-for-video", "30-300"]
FIRST_PART_SUFFIX = " (part 1)"
# yt-dlp adds the date and time to a live stream's title ("Title 2026-11-03 17_30");
# fulltitle is the title without it.
TITLE_ARGS = ["--parse-metadata", "fulltitle:%(title)s"]

Outcome = tuple[JobStatus, str | None]
# A part whose links expired sooner than this isn't continued: something else is wrong.
MIN_EXPIRED_PART_SECONDS = 600


@dataclass(frozen=True)
class PartWatch:
    """What the recorder hears from a running part."""

    on_start: Callable[[asyncio.subprocess.Process], None]
    on_progress: Callable[[ProgressUpdate], None]
    # The part's finished file was saved (yt-dlp's after_move print).
    on_file: Callable[[], None]


RunPart = Callable[[list[str], PartWatch], Awaitable[ProcessResult]]


def part_template(template: str | None, part: int) -> str:
    """The file name template with " (part N)" before the extension."""
    base = template or DEFAULT_OUTPUT
    if base.endswith(EXT_SUFFIX):
        return f"{base.removesuffix(EXT_SUFFIX)} (part {part}){EXT_SUFFIX}"
    return f"{base} (part {part})"


def part_args(job: Job, part: int) -> list[str]:
    """Only the first part records from the stream's start; later ones continue from now."""
    args = [*TITLE_ARGS, *WAIT_ARGS]
    if part == 1 and job.record_from_start:
        args = ["--live-from-start", *args]
    # Most recordings are one file, so the first part keeps the plain name; it becomes
    # "(part 1)" only once a second part starts (see number_first_part).
    if part > 1:
        args += ["--output", part_template(output_template(job), part)]
    return args


def number_first_part(filepath: str) -> str:
    """Renames the first part's file, and files saved beside it with the same name (its
    .nfo and thumbnail), to "… (part 1)". Returns the file's new path."""
    path = Path(filepath)
    stem = path.stem
    # Already numbered: recorded by an older version, which numbered every split part.
    if not path.exists() or stem.endswith(FIRST_PART_SUFFIX):
        return filepath
    for sibling in path.parent.iterdir():
        if sibling.is_file() and sibling.name.startswith(f"{stem}."):
            rest = sibling.name.removeprefix(stem)
            sibling.rename(sibling.with_name(f"{stem}{FIRST_PART_SUFFIX}{rest}"))
    return str(path.with_name(f"{stem}{FIRST_PART_SUFFIX}{path.suffix}"))


@dataclass
class PartTimer:
    """Stops the running part when its time is up."""

    seconds: float | None
    timed_out: bool = False
    _handle: asyncio.TimerHandle | None = None
    _process: asyncio.subprocess.Process | None = None

    def start(self, process: asyncio.subprocess.Process) -> None:
        self._process = process
        if self.seconds is not None:
            self._handle = asyncio.get_running_loop().call_later(self.seconds, self.stop)

    def stop(self) -> None:
        # Once only: a second SIGINT would make yt-dlp give up merging the file.
        if self._process is not None and not self.timed_out:
            self.timed_out = True
            interrupt_process(self._process)

    def cancel(self) -> None:
        if self._handle is not None:
            self._handle.cancel()


def part_length(job: Job, saved: float) -> float | None:
    """How long the next part may run: its own length, capped by what max_seconds leaves."""
    lengths: list[float] = [job.part_seconds] if job.part_seconds else []
    if job.max_seconds:
        lengths.append(max(0.0, job.max_seconds - saved))
    return min(lengths) if lengths else None


def _clock(job: Job, part: int) -> StreamClock:
    """Parts recorded from the start of a stream that was already live when found count
    its fragments. (For streams found before they started, scheduled_at is only the
    announced start, so the time spent is the better measure.)"""
    from_start = part == 1 and job.record_from_start
    was_live = job.scheduled_at is not None and as_utc(job.scheduled_at) <= as_utc(job.created_at)
    return StreamClock(job.scheduled_at if from_start and was_live else None)


def _part_outcome(result: ProcessResult, cancelled: bool, saved_file: bool) -> Outcome:
    if cancelled:
        return JobStatus.CANCELLED, None
    # When a stream ends, its last fragments are often gone: yt-dlp logs "Did not get any
    # data blocks" and exits with an error after saving the file. The recording is fine.
    if result.returncode == 0 or saved_file:
        return JobStatus.COMPLETED, None
    return JobStatus.FAILED, result.error or f"yt-dlp exited with code {result.returncode}."


@dataclass(frozen=True)
class RecordingHooks:
    run_part: RunPart
    on_start: Callable[[asyncio.subprocess.Process], None]
    is_cancelled: Callable[[], bool]
    # Saves the job (its part number) before each part starts.
    on_part: Callable[[int], Awaitable[None]]
    # Whether the stream is still live (asked after a part's links expired).
    still_live: Callable[[], Awaitable[bool]]


@dataclass
class _Part:
    """One running part: stops it when its time is up or the maximum length is saved."""

    clock: StreamClock
    timer: PartTimer
    # Seconds of the stream still to save, when the recording has a maximum length.
    left: float | None
    on_process: Callable[[asyncio.subprocess.Process], None]
    saved_file: bool = False

    def watch(self) -> PartWatch:
        return PartWatch(self._on_start, self._on_progress, self._on_file)

    def _on_file(self) -> None:
        self.saved_file = True

    def _on_start(self, process: asyncio.subprocess.Process) -> None:
        self.on_process(process)
        self.timer.start(process)

    def _on_progress(self, update: ProgressUpdate) -> None:
        self.clock.update(update)
        if self.left is not None and self.clock.seconds() >= self.left:
            self.timer.stop()


async def _links_expired_while_live(
    result: ProcessResult, seconds: float, hooks: RecordingHooks
) -> bool:
    if not result.links_expired or seconds < MIN_EXPIRED_PART_SECONDS:
        return False
    return await hooks.still_live()


async def record(job: Job, hooks: RecordingHooks) -> Outcome:
    # After a restart the recording continues with the next part.
    part = (job.part or 0) + 1
    saved = 0.0  # Seconds of the stream saved by finished parts.
    while True:
        await hooks.on_part(part)
        left = job.max_seconds - saved if job.max_seconds else None
        running = _Part(_clock(job, part), PartTimer(part_length(job, saved)), left, hooks.on_start)
        started = time.monotonic()
        try:
            result = await hooks.run_part(part_args(job, part), running.watch())
        finally:
            running.timer.cancel()
        saved += running.clock.seconds()
        # A part stopped by its timer ends normally, and so does one whose links expired
        # while the stream is still live; anything else ends the recording.
        if hooks.is_cancelled():
            return _part_outcome(result, True, running.saved_file)
        if not running.timer.timed_out and not await _links_expired_while_live(
            result, time.monotonic() - started, hooks
        ):
            return _part_outcome(result, False, running.saved_file)
        if job.max_seconds and saved >= job.max_seconds:
            return JobStatus.COMPLETED, None
        part += 1
