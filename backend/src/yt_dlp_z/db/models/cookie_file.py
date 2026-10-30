from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.db.models.job import utcnow


class CookieFile(Base):
    """An uploaded cookies.txt. The contents live on disk, never in the DB or the API."""

    __tablename__ = "cookie_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    cookie_count: Mapped[int] = mapped_column(Integer)
    domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
