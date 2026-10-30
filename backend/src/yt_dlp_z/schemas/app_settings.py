from typing import Annotated

from pydantic import BaseModel, Field

MAX_CONCURRENT_DOWNLOADS = 10
MAX_SUBSCRIPTIONS = 100
MAX_RECORDING_HOURS = 24 * 7
Hours = Annotated[int, Field(ge=1, le=MAX_RECORDING_HOURS)]


class RecordingSettings(BaseModel):
    """How live streams are recorded. Hours; None turns a setting off. Every recording
    keeps the values it started with."""

    # Start a new file every this many hours, so endless streams stay manageable.
    part_hours: Hours | None
    # Stop recording after this many hours.
    max_hours: Hours | None
    # Record from the start, unless the stream has been live longer than this when
    # found; then record from now (yt-dlp would otherwise fetch days of a 24/7 stream).
    from_start_max_hours: Hours | None


DEFAULT_RECORDING = RecordingSettings(part_hours=6, max_hours=None, from_start_max_hours=6)


class AppSettings(BaseModel):
    download_dir: str = Field(min_length=1, max_length=4096)
    max_concurrent_downloads: int = Field(ge=1, le=MAX_CONCURRENT_DOWNLOADS)
    # Live recordings running at once, counted apart from downloads.
    max_concurrent_recordings: int = Field(ge=1, le=MAX_CONCURRENT_DOWNLOADS)
    # Watched channels. Above the default of 5, YouTube may rate-limit or flag the IP.
    max_subscriptions: int = Field(ge=1, le=MAX_SUBSCRIPTIONS)
    recording: RecordingSettings
