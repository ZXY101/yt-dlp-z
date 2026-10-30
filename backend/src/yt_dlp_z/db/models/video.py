from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.db.models.job import utcnow


class VideoState(StrEnum):
    QUEUED = "queued"  # a download job was created
    SKIPPED = "skipped"  # a filter rejected it, or it predates the backfill
    UPCOMING = "upcoming"  # scheduled stream or premiere (recorded from milestone 5)
    LIVE = "live"  # live right now (recorded from milestone 5)
    FAILED = "failed"  # yt-dlp couldn't read it; retried on the next check


class Video(Base):
    """A feed entry a subscription has seen, so each video is handled only once."""

    __tablename__ = "videos"
    __table_args__ = (UniqueConstraint("subscription_id", "video_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True
    )
    video_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    state: Mapped[VideoState] = mapped_column(String(20))
    # Why it was skipped or failed, shown in the UI.
    reason: Mapped[str | None] = mapped_column(Text, default=None)
    live_status: Mapped[str | None] = mapped_column(String(20), default=None)
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    job_id: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
