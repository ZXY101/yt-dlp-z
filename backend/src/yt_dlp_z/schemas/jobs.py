from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from yt_dlp_z.db.models.job import JobKind, JobStatus
from yt_dlp_z.schemas.common import WebUrl, as_utc_iso
from yt_dlp_z.schemas.recording import Hours

OptionValue = bool | int | float | str | list[str]


class RecordingRequest(BaseModel):
    """Records a live or upcoming stream instead of downloading. The form fills these in
    from the live-stream preset."""

    from_start: bool
    # Upcoming streams: when they start (from the link check). The recording waits until then.
    starts_at: datetime | None = None
    # A new file every this many hours, and stop after this many. None: off.
    part_hours: Hours | None = None
    max_hours: Hours | None = None


class JobCreate(BaseModel):
    url: WebUrl
    # Known from the link check; shown until yt-dlp reports its own.
    title: str | None = Field(default=None, max_length=500)
    recording: RecordingRequest | None = None
    # Keyed by yt-dlp long flag, e.g. {"--format": "bv*+ba", "--embed-subs": true}.
    options: dict[str, OptionValue] = {}
    extra_args: str = Field(default="", max_length=4000)
    # Empty: the default download folder. Relative: inside it. Absolute: inside an allowed root.
    output_dir: str | None = Field(default=None, max_length=4096)
    # An uploaded cookies file; yt-dlp-z passes --cookies itself.
    cookie_id: int | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status: JobStatus
    kind: JobKind
    # When a scheduled recording's stream is due to start.
    scheduled_at: datetime | None
    # Recordings: settings they started with, and the part being recorded.
    record_from_start: bool
    part_seconds: int | None
    max_seconds: int | None
    part: int | None
    options: dict[str, OptionValue]
    extra_args: str
    output_dir: str
    cookie_id: int | None
    # The channel subscription that queued it, if any.
    subscription_id: int | None
    title: str | None
    progress: float | None
    downloaded_bytes: int | None
    total_bytes: int | None
    speed: float | None
    eta: int | None
    filepath: str | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    revision: int

    @field_serializer("created_at", "scheduled_at", "started_at", "finished_at")
    def as_utc(self, value: datetime | None) -> str | None:
        return as_utc_iso(value)


class JobEvent(BaseModel):
    type: Literal["job"] = "job"
    job: JobOut


class JobDeletedEvent(BaseModel):
    type: Literal["job_deleted"] = "job_deleted"
    id: int
