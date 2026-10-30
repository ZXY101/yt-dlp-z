from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from yt_dlp_z.db.models.job import JobStatus

OptionValue = bool | int | float | str | list[str]


class JobCreate(BaseModel):
    url: str = Field(max_length=4096)
    # Keyed by yt-dlp long flag, e.g. {"--format": "bv*+ba", "--embed-subs": true}.
    options: dict[str, OptionValue] = {}
    extra_args: str = Field(default="", max_length=4000)
    # Empty: the default download folder. Relative: inside it. Absolute: inside an allowed root.
    output_dir: str | None = Field(default=None, max_length=4096)

    @field_validator("url")
    @classmethod
    def must_be_web_url(cls, url: str) -> str:
        url = url.strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter a web address starting with http:// or https://")
        return url


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status: JobStatus
    options: dict[str, OptionValue]
    extra_args: str
    output_dir: str
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

    @field_serializer("created_at", "started_at", "finished_at")
    def as_utc(self, value: datetime | None) -> str | None:
        # SQLite drops timezone info; stored values are always UTC.
        if value is None:
            return None
        return value.replace(tzinfo=value.tzinfo or UTC).isoformat()


class JobEvent(BaseModel):
    type: Literal["job"] = "job"
    job: JobOut


class JobDeletedEvent(BaseModel):
    type: Literal["job_deleted"] = "job_deleted"
    id: int
