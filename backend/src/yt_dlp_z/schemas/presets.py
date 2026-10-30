from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from yt_dlp_z.schemas.common import Name, as_utc_iso
from yt_dlp_z.schemas.jobs import OptionValue


class PresetIn(BaseModel):
    name: Name
    options: dict[str, OptionValue] = {}
    extra_args: str = Field(default="", max_length=4000)
    output_dir: str | None = Field(default=None, max_length=4096)
    cookie_id: int | None = None
    # Making one preset the default clears the flag on the others.
    is_default: bool = False

    @field_validator("output_dir")
    @classmethod
    def empty_means_default(cls, output_dir: str | None) -> str | None:
        return (output_dir or "").strip() or None


class PresetOut(PresetIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def as_utc(self, value: datetime) -> str | None:
        return as_utc_iso(value)
