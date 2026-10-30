from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.preset import Preset
from yt_dlp_z.schemas.presets import PresetIn


class DuplicatePresetError(ValueError):
    pass


async def list_presets(session: AsyncSession) -> Sequence[Preset]:
    result = await session.execute(select(Preset).order_by(Preset.name))
    return result.scalars().all()


async def get_preset(session: AsyncSession, preset_id: int) -> Preset | None:
    return await session.get(Preset, preset_id)


async def save_preset(session: AsyncSession, preset: Preset, values: PresetIn) -> Preset:
    """Creates or updates a preset. Names must be unique; only one preset is the default."""
    for name, value in values.model_dump().items():
        setattr(preset, name, value)
    if values.is_default:
        await session.execute(update(Preset).where(Preset.id != preset.id).values(is_default=False))
    session.add(preset)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise DuplicatePresetError(f"A preset named {values.name!r} already exists") from error
    await session.refresh(preset)
    return preset


async def delete_preset(session: AsyncSession, preset: Preset) -> None:
    await session.delete(preset)
    await session.commit()
