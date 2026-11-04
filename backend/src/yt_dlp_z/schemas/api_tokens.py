from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from yt_dlp_z.schemas.common import Name, as_utc_iso


class ApiTokenCreate(BaseModel):
    name: Name


class ApiTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    last_used_at: datetime | None

    @field_serializer("created_at")
    def created_as_utc(self, value: datetime) -> str:
        return as_utc_iso(value)

    @field_serializer("last_used_at")
    def used_as_utc(self, value: datetime | None) -> str | None:
        return as_utc_iso(value) if value else None


class ApiTokenCreated(ApiTokenOut):
    """The only response that ever holds the token itself."""

    token: str
