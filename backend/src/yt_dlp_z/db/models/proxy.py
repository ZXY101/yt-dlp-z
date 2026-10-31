from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.db.models.job import utcnow


class Proxy(Base):
    """An HTTP or SOCKS proxy in the proxy pool (services/proxies)."""

    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # May hold a user name and password: the API only returns it masked.
    url: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Skipped until then: YouTube blocked or rate-limited a download through it.
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # The last "Test": whether it worked, the IP sites saw, or what went wrong.
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    check_ok: Mapped[bool | None] = mapped_column(Boolean, default=None)
    exit_ip: Mapped[str | None] = mapped_column(String(100), default=None)
    check_error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
