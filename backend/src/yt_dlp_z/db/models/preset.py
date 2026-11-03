from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.db.models.job import utcnow
from yt_dlp_z.schemas.common import FileNaming, FolderLayout, ProxyMode


class Preset(Base):
    """A saved set of download options, applied to the download form or a subscription."""

    __tablename__ = "presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # Same format as Job.options: keyed by yt-dlp long flag.
    options: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    extra_args: Mapped[str] = mapped_column(Text, default="")
    # Cleared when that cookies file is deleted.
    cookie_id: Mapped[int | None] = mapped_column(Integer, default=None)
    # Stored as entered (relative or absolute) and resolved when a job starts.
    output_dir: Mapped[str | None] = mapped_column(Text, default=None)
    # See schemas/presets.py PresetKind. The default preset is the default for its kind.
    kind: Mapped[str] = mapped_column(String(20), default="any", server_default="any")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    # Live-stream presets: schemas/recording.py RecordingSettings.
    recording: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    # Layout: schemas/common.py FolderLayout and FileNaming, None for the plain default.
    folders: Mapped[FolderLayout | None] = mapped_column(String(20), default=None)
    file_name: Mapped[FileNaming | None] = mapped_column(String(20), default=None)
    media_files: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    proxy_mode: Mapped[ProxyMode] = mapped_column(String(20), default="off", server_default="off")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
