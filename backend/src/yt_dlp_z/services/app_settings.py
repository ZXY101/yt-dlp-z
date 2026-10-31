"""Settings changed from the Settings page. Env vars give the defaults until then."""

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.schemas.ytdlp import YtdlpPreferences
from yt_dlp_z.services.settings_store import get_value, set_values

MAX_CONCURRENT_DOWNLOADS = "max_concurrent_downloads"
MAX_CONCURRENT_RECORDINGS = "max_concurrent_recordings"
MAX_SUBSCRIPTIONS = "max_subscriptions"
# Watching more channels than this from one IP risks YouTube rate limits.
DEFAULT_MAX_SUBSCRIPTIONS = 5


async def get_max_concurrent_downloads(session: AsyncSession, default: int) -> int:
    value = await get_value(session, MAX_CONCURRENT_DOWNLOADS)
    return int(value) if value else default


async def set_max_concurrent_downloads(session: AsyncSession, limit: int) -> None:
    await set_values(session, {MAX_CONCURRENT_DOWNLOADS: str(limit)})


async def get_max_concurrent_recordings(session: AsyncSession, default: int) -> int:
    value = await get_value(session, MAX_CONCURRENT_RECORDINGS)
    return int(value) if value else default


async def set_max_concurrent_recordings(session: AsyncSession, limit: int) -> None:
    await set_values(session, {MAX_CONCURRENT_RECORDINGS: str(limit)})


async def get_max_subscriptions(session: AsyncSession) -> int:
    value = await get_value(session, MAX_SUBSCRIPTIONS)
    return int(value) if value else DEFAULT_MAX_SUBSCRIPTIONS


async def set_max_subscriptions(session: AsyncSession, limit: int) -> None:
    await set_values(session, {MAX_SUBSCRIPTIONS: str(limit)})


YTDLP_CHANNEL = "ytdlp_channel"
YTDLP_AUTO_UPDATE = "ytdlp_auto_update"


async def get_ytdlp_preferences(session: AsyncSession) -> YtdlpPreferences:
    channel = await get_value(session, YTDLP_CHANNEL)
    auto_update = await get_value(session, YTDLP_AUTO_UPDATE)
    return YtdlpPreferences(
        channel="nightly" if channel == "nightly" else "stable",
        # Off unless turned on: an update changes what every later download runs.
        auto_update=auto_update == "true",
    )


async def set_ytdlp_preferences(session: AsyncSession, preferences: YtdlpPreferences) -> None:
    auto_update = "true" if preferences.auto_update else "false"
    await set_values(session, {YTDLP_CHANNEL: preferences.channel, YTDLP_AUTO_UPDATE: auto_update})
