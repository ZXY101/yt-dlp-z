"""Settings changed from the Settings page. Env vars give the defaults until then."""

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.schemas.app_settings import DEFAULT_RECORDING, RecordingSettings
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


# Hours; empty means "off". Unset keys fall back to RecordingSettings' defaults.
RECORDING_KEYS = {
    "part_hours": "recording_part_hours",
    "max_hours": "recording_max_hours",
    "from_start_max_hours": "recording_from_start_max_hours",
}
LONG_STREAMS = "recording_long_streams"


async def get_recording_settings(session: AsyncSession) -> RecordingSettings:
    values = DEFAULT_RECORDING.model_dump()
    for field, key in RECORDING_KEYS.items():
        stored = await get_value(session, key)
        if stored is not None:
            values[field] = int(stored) if stored else None
    values["long_streams"] = await get_value(session, LONG_STREAMS) or values["long_streams"]
    return RecordingSettings.model_validate(values)


async def set_recording_settings(session: AsyncSession, recording: RecordingSettings) -> None:
    stored = recording.model_dump()
    values = {key: str(stored[field] or "") for field, key in RECORDING_KEYS.items()}
    values[LONG_STREAMS] = recording.long_streams
    await set_values(session, values)
