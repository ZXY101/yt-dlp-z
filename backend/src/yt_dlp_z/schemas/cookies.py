from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from yt_dlp_z.schemas.common import Name, WebUrl, as_utc_iso

MAX_COOKIE_FILE_CHARS = 1_000_000


class CookieFileUpdate(BaseModel):
    name: Name
    # The cookies.txt text, stored on disk and never returned by the API.
    # Leave out when updating to keep the current file and only rename it.
    content: str | None = Field(default=None, min_length=1, max_length=MAX_COOKIE_FILE_CHARS)


class CookieFileCreate(CookieFileUpdate):
    content: str = Field(min_length=1, max_length=MAX_COOKIE_FILE_CHARS)


class CookieFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cookie_count: int
    domains: list[str]
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def as_utc(self, value: datetime) -> str | None:
        return as_utc_iso(value)


class CookieCheckRequest(BaseModel):
    # A page that only works when signed in, e.g. a members-only video.
    url: WebUrl


class CookieCheckResult(BaseModel):
    ok: bool
    message: str
