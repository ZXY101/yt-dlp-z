"""Turns the recording settings into what one recording job does."""

from dataclasses import dataclass
from datetime import datetime

from yt_dlp_z.schemas.app_settings import RecordingSettings

SECONDS_PER_HOUR = 3600


@dataclass(frozen=True)
class RecordingPlan:
    record_from_start: bool
    part_seconds: int | None
    max_seconds: int | None


def _seconds(hours: int | None) -> int | None:
    return hours * SECONDS_PER_HOUR if hours else None


def plan_recording(
    settings: RecordingSettings, live_since: datetime | None, now: datetime
) -> RecordingPlan:
    """`live_since`: when the stream went live, for streams already live when found."""
    from_start = True
    limit = _seconds(settings.from_start_max_hours)
    if live_since is not None and limit is not None:
        if live_since.tzinfo is None:  # SQLite drops the timezone; stored values are UTC.
            live_since = live_since.replace(tzinfo=now.tzinfo)
        from_start = (now - live_since).total_seconds() <= limit
    return RecordingPlan(
        record_from_start=from_start,
        part_seconds=_seconds(settings.part_hours),
        max_seconds=_seconds(settings.max_hours),
    )
