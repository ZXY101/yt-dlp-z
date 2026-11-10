from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from yt_dlp_z.db.models.job import JobKind, JobStatus
from yt_dlp_z.schemas.common import WebUrl, as_utc_iso
from yt_dlp_z.schemas.jobs import JobOut


class SendRequest(BaseModel):
    """A link to download with a preset; the server works out the rest."""

    url: WebUrl
    # Empty: the default preset for this kind of link.
    preset_id: int | None = None
    # Required to download a whole playlist or channel. For a video opened from a playlist
    # (watch?v=…&list=…), picks the playlist instead of the video alone.
    whole_playlist: bool = False


class SentLink(BaseModel):
    job: JobOut
    # The preset used, if any.
    preset: str | None
    # True when the same link with the same settings was already queued, running or
    # downloaded: `job` is that job and nothing new was queued.
    existing: bool = False


class LinkJobsRequest(BaseModel):
    url: WebUrl
    # For a video opened from a playlist: the playlist's jobs instead of the video's.
    whole_playlist: bool = False


class LinkJob(BaseModel):
    """A job's progress, without its files or settings: send-only tokens can read this."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: JobStatus
    kind: JobKind
    title: str | None
    progress: float | None
    downloaded_bytes: int | None
    total_bytes: int | None
    speed: float | None
    eta: int | None
    part: int | None
    scheduled_at: datetime | None
    error: str | None
    created_at: datetime
    finished_at: datetime | None

    @field_serializer("scheduled_at", "created_at", "finished_at")
    def as_utc(self, value: datetime | None) -> str | None:
        return as_utc_iso(value)


class LinkJobs(BaseModel):
    # Newest first.
    jobs: list[LinkJob]
