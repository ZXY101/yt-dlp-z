"""Settings changed from the Settings page. Env vars give the defaults until then."""

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.services.settings_store import get_value, set_values

MAX_CONCURRENT_DOWNLOADS = "max_concurrent_downloads"


async def get_max_concurrent_downloads(session: AsyncSession, default: int) -> int:
    value = await get_value(session, MAX_CONCURRENT_DOWNLOADS)
    return int(value) if value else default


async def set_max_concurrent_downloads(session: AsyncSession, limit: int) -> None:
    await set_values(session, {MAX_CONCURRENT_DOWNLOADS: str(limit)})
