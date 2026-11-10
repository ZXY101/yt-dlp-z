from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.db.models.job import utcnow


class TokenScope(StrEnum):
    # Everything a signed-in browser can do, except manage tokens.
    FULL = "full"
    # Only what a "send this link" client needs: list presets, check a link, send it.
    SEND = "send"


class ApiToken(Base):
    """Lets a script or an AI agent use the API without the admin password. Only the hash
    is stored, so a token can be shown once and never again."""

    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    scope: Mapped[TokenScope] = mapped_column(
        String(10), default=TokenScope.FULL, server_default=TokenScope.FULL.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
