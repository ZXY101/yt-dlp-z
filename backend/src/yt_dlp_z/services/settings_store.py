from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.setting import Setting


async def get_value(session: AsyncSession, key: str) -> str | None:
    result = await session.execute(select(Setting.value).where(Setting.key == key))
    return result.scalar_one_or_none()


async def set_values(session: AsyncSession, values: dict[str, str]) -> None:
    for key, value in values.items():
        await session.merge(Setting(key=key, value=value))
    await session.commit()
