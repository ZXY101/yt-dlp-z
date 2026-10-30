from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.db.models.job import utcnow


class Preset(Base):
    """A saved set of download options, applied to the download form or a subscription."""

    __tablename__ = "presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # Same format as Job.options: keyed by yt-dlp long flag.
    options: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    extra_args: Mapped[str] = mapped_column(Text, default="")
    # Stored as entered (relative or absolute) and resolved when a job starts.
    output_dir: Mapped[str | None] = mapped_column(Text, default=None)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
