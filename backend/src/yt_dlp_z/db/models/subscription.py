from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.db.models.job import utcnow


class Subscription(Base):
    """A watched YouTube channel or playlist. New videos are filtered and queued with its
    preset."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # "channel" or "playlist" (channel_id then holds the playlist id).
    kind: Mapped[str] = mapped_column(String(20), default="channel", server_default="channel")
    channel_id: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    # Cleared when the preset or cookies file is deleted.
    preset_id: Mapped[int | None] = mapped_column(Integer, default=None)
    # Live streams and premieres use this preset when set (its options and recording
    # settings); else preset_id's options and the default live-stream preset's recording.
    stream_preset_id: Mapped[int | None] = mapped_column(Integer, default=None)
    cookie_id: Mapped[int | None] = mapped_column(Integer, default=None)
    # Overrides the preset's folder. Stored as entered and resolved per download.
    output_dir: Mapped[str | None] = mapped_column(Text, default=None)
    # See schemas/subscriptions.py SubscriptionFilters.
    filters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    poll_minutes: Mapped[int] = mapped_column(Integer)
    # How many of the newest feed entries the first check may download (0: only new ones).
    backfill: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Delete its downloads this many days after they finish (None: keep them).
    keep_days: Mapped[int | None] = mapped_column(Integer, default=None)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_error: Mapped[str | None] = mapped_column(Text, default=None)
    # Last look at the channel's /streams tab, for streams the RSS feed missed.
    streams_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
