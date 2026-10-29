from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from yt_dlp_z.core.config import Settings
from yt_dlp_z.core.rate_limit import FailureRateLimiter
from yt_dlp_z.core.security import SessionSigner


@dataclass
class AppState:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    signer: SessionSigner
    login_limiter: FailureRateLimiter = field(default_factory=FailureRateLimiter)
