from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.preset import Preset
from yt_dlp_z.schemas.presets import PresetIn, PresetKind
from yt_dlp_z.schemas.recording import DEFAULT_RECORDING, RecordingSettings
from yt_dlp_z.services.watch.store import unlink_preset


class DuplicatePresetError(ValueError):
    pass


async def list_presets(session: AsyncSession) -> Sequence[Preset]:
    result = await session.execute(select(Preset).order_by(Preset.name))
    return result.scalars().all()


async def get_preset(session: AsyncSession, preset_id: int) -> Preset | None:
    return await session.get(Preset, preset_id)


async def save_preset(session: AsyncSession, preset: Preset, values: PresetIn) -> Preset:
    """Creates or updates a preset. Names must be unique; each kind has one default."""
    for name, value in values.model_dump().items():
        setattr(preset, name, value)
    if values.is_default:
        others = (Preset.id != preset.id) & (Preset.kind == values.kind)
        await session.execute(update(Preset).where(others).values(is_default=False))
    session.add(preset)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise DuplicatePresetError(f"A preset named {values.name!r} already exists") from error
    await session.refresh(preset)
    return preset


async def delete_preset(session: AsyncSession, preset: Preset) -> None:
    await unlink_preset(session, preset.id)
    await session.delete(preset)
    await session.commit()


async def default_preset(session: AsyncSession, kind: PresetKind) -> Preset | None:
    result = await session.execute(
        select(Preset).where(Preset.kind == kind, Preset.is_default).limit(1)
    )
    return result.scalar_one_or_none()


def preset_recording(preset: Preset | None) -> RecordingSettings | None:
    if preset is None or preset.recording is None:
        return None
    return RecordingSettings.model_validate(preset.recording)


async def default_recording(session: AsyncSession) -> RecordingSettings:
    """The default live-stream preset's recording settings."""
    preset = await default_preset(session, "live")
    return preset_recording(preset) or DEFAULT_RECORDING
