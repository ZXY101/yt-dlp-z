from datetime import datetime
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from yt_dlp_z.schemas.common import FileNaming, FolderLayout, Name, ProxyMode, as_utc_iso
from yt_dlp_z.schemas.jobs import OptionValue
from yt_dlp_z.schemas.live_chat import LiveChatSettings
from yt_dlp_z.schemas.recording import DEFAULT_RECORDING, RecordingSettings

# Which links a preset is made for. "playlist" covers playlists and channels, "live"
# live and upcoming streams.
PresetKind = Literal["any", "video", "playlist", "live"]


class PresetIn(BaseModel):
    name: Name
    options: dict[str, OptionValue] = {}
    extra_args: str = Field(default="", max_length=4000)
    output_dir: str | None = Field(default=None, max_length=4096)
    cookie_id: int | None = None
    # Folder and file-name layout, and the thumbnail and .nfo files media servers read.
    folders: FolderLayout | None = None
    file_name: FileNaming | None = None
    media_files: bool = False
    proxy_mode: ProxyMode = "off"
    live_chat: LiveChatSettings | None = None
    kind: PresetKind = "any"
    # The default for its kind of link. Making one preset the default clears the flag on
    # the others of the same kind.
    is_default: bool = False
    # Live-stream presets only; they always have them.
    recording: RecordingSettings | None = None

    @field_validator("output_dir")
    @classmethod
    def empty_means_default(cls, output_dir: str | None) -> str | None:
        return (output_dir or "").strip() or None

    @model_validator(mode="after")
    def recording_for_live_only(self) -> Self:
        if self.kind != "live":
            self.recording = None
        elif self.recording is None:
            self.recording = DEFAULT_RECORDING
        return self


class PresetOut(PresetIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def as_utc(self, value: datetime) -> str:
        return as_utc_iso(value)
