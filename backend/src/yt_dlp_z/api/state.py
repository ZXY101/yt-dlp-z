from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from yt_dlp_z.core.config import Settings
from yt_dlp_z.core.rate_limit import FailureRateLimiter
from yt_dlp_z.core.security import SessionSigner
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.jobs.manager import JobManager
from yt_dlp_z.services.watch.watcher import SubscriptionWatcher
from yt_dlp_z.services.ytdlp.schema import OptionSchemaProvider


@dataclass
class AppState:
    settings: Settings
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]
    signer: SessionSigner
    hub: EventHub
    schemas: OptionSchemaProvider
    jobs: JobManager
    watcher: SubscriptionWatcher
    login_limiter: FailureRateLimiter = field(default_factory=FailureRateLimiter)
