from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from yt_dlp_z.schemas.common import as_utc_iso
from yt_dlp_z.schemas.jobs import OptionValue


class PresetIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    options: dict[str, OptionValue] = {}
    extra_args: str = Field(default="", max_length=4000)
    output_dir: str | None = Field(default=None, max_length=4096)
    # Making one preset the default clears the flag on the others.
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def must_not_be_blank(cls, name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("Give the preset a name")
        return name

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
