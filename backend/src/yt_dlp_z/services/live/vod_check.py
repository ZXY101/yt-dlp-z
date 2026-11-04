"""Decides whether a VOD can safely replace its recording.

Creators sometimes cut parts out of a stream's VOD, and YouTube itself keeps only the first
12 hours of very long ones, so the recording can hold more than the VOD. A cut shows up as a VOD
shorter than the recording, or than the time the stream ran (for a recording that started
late). Anything that can't be measured counts as not safe: an extra file is easily deleted, and
a deleted recording can't be brought back. An edit that keeps the length, such as muting or
blurring, can't be seen this way.
"""

import asyncio
import logging
from pathlib import Path

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.services.live.stream_clock import as_utc

logger = logging.getLogger(__name__)

FFPROBE_TIMEOUT_SECONDS = 60
# Recordings and VODs of the same stream differ a little at the ends.
FILE_TOLERANCE_SECONDS = 60
# Time the stream ran is measured to when the recording finished, merging included.
RUNTIME_TOLERANCE_SECONDS = 300
RUNTIME_TOLERANCE_SHARE = 0.02
SECONDS_PER_MINUTE = 60


async def media_seconds(path: Path) -> float | None:
    """A media file's length, or None if ffprobe can't tell."""
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            "--",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        output, _ = await asyncio.wait_for(process.communicate(), FFPROBE_TIMEOUT_SECONDS)
        return float(output.strip())
    except (OSError, ValueError, TimeoutError):
        logger.warning("Couldn't measure %s", path, exc_info=True)
        return None


async def _total_seconds(files: list[str]) -> float | None:
    if not files:
        return None
    lengths = [await media_seconds(Path(file)) for file in files]
    known = [length for length in lengths if length is not None]
    return sum(known) if len(known) == len(lengths) else None


def _stream_runtime(recording: Job) -> float | None:
    """At least how long the stream ran: a stopped recording's stream may have gone on."""
    if recording.stream_started is None or recording.finished_at is None:
        return None
    return as_utc(recording.finished_at).timestamp() - recording.stream_started


def _minutes_short(seconds: float) -> str:
    return f"{max(1, round(seconds / SECONDS_PER_MINUTE))} min"


async def reason_to_keep(recording: Job, vod: Job) -> str | None:
    """Why the recording should stay, or None if the VOD can replace it."""
    vod_length = await _total_seconds(vod.files)
    recorded = await _total_seconds(recording.files)
    if vod_length is None or recorded is None:
        return "Recording kept: couldn't compare its length with the VOD's."
    if recorded - vod_length > FILE_TOLERANCE_SECONDS:
        short = _minutes_short(recorded - vod_length)
        return f"Recording kept: the VOD is {short} shorter, so it may have been edited."
    runtime = _stream_runtime(recording)
    if runtime is not None:
        allowed = max(RUNTIME_TOLERANCE_SECONDS, runtime * RUNTIME_TOLERANCE_SHARE)
        if runtime - vod_length > allowed:
            short = _minutes_short(runtime - vod_length)
            return (
                f"Recording kept: the VOD is {short} shorter than the stream ran, "
                "so it may have been edited."
            )
    return None
