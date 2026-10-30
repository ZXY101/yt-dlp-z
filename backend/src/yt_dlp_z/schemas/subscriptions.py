import re
from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from yt_dlp_z.db.models.video import VideoState
from yt_dlp_z.schemas.common import as_utc_iso

# Polling more often than this risks YouTube rate-limiting or flagging the IP.
MIN_POLL_MINUTES = 5
MAX_POLL_MINUTES = 7 * 24 * 60
DEFAULT_POLL_MINUTES = 10
# The channel RSS feed only lists the newest 15 uploads.
MAX_BACKFILL = 15


class ContentType(StrEnum):
    VIDEO = "video"
    SHORT = "short"
    # Live streams and premieres (yt-dlp reports both through live_status).
    STREAM = "stream"


def _check_regex(pattern: str | None) -> str | None:
    pattern = (pattern or "").strip() or None
    if pattern is None:
        return None
    try:
        re.compile(pattern)
    except re.error as error:
        raise ValueError(f"Not a valid regular expression: {error}") from error
    return pattern


class SubscriptionFilters(BaseModel):
    """Which new uploads get downloaded. Empty or unset fields don't filter."""

    content_types: list[ContentType] = [ContentType.VIDEO]
    # Case-insensitive regular expressions matched anywhere in the title.
    title_include: str | None = Field(default=None, max_length=500)
    title_exclude: str | None = Field(default=None, max_length=500)
    min_duration: int | None = Field(default=None, ge=0, description="Seconds")
    max_duration: int | None = Field(default=None, ge=0, description="Seconds")
    published_after: date | None = None
    include_members_only: bool = False

    _regex = field_validator("title_include", "title_exclude")(_check_regex)

    @model_validator(mode="after")
    def check_ranges(self) -> Self:
        if not self.content_types:
            raise ValueError("Pick at least one content type")
        low, high = self.min_duration, self.max_duration
        if low is not None and high is not None and low > high:
            raise ValueError("The minimum duration is longer than the maximum")
        return self


class SubscriptionUpdate(BaseModel):
    preset_id: int | None = None
    cookie_id: int | None = None
    # Empty: the preset's folder (or the default). Same rules as a download's folder.
    output_dir: str | None = Field(default=None, max_length=4096)
    filters: SubscriptionFilters = SubscriptionFilters()
    poll_minutes: int = Field(
        default=DEFAULT_POLL_MINUTES, ge=MIN_POLL_MINUTES, le=MAX_POLL_MINUTES
    )
    enabled: bool = True

    @field_validator("output_dir")
    @classmethod
    def empty_means_default(cls, output_dir: str | None) -> str | None:
        return (output_dir or "").strip() or None


class SubscriptionCreate(SubscriptionUpdate):
    # A channel URL, or just its @handle.
    channel: str = Field(min_length=1, max_length=4096)
    # How many of the newest uploads to download now. 0: only uploads from now on.
    backfill: int = Field(default=0, ge=0, le=MAX_BACKFILL)


class SubscriptionOut(SubscriptionUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: str
    name: str
    url: str
    backfill: int
    last_checked_at: datetime | None
    last_error: str | None
    created_at: datetime
    # A check is running right now.
    checking: bool = False

    @field_serializer("last_checked_at", "created_at")
    def as_utc(self, value: datetime | None) -> str | None:
        return as_utc_iso(value)


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: str
    title: str
    published_at: datetime | None
    state: VideoState
    reason: str | None
    live_status: str | None
    release_at: datetime | None
    job_id: int | None
    updated_at: datetime

    @field_serializer("published_at", "release_at", "updated_at")
    def as_utc(self, value: datetime | None) -> str | None:
        return as_utc_iso(value)
