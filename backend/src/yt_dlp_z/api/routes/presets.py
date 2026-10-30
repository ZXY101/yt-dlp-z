from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.validation import check_cookie_id, check_output_dir, check_user_args
from yt_dlp_z.db.models.preset import Preset
from yt_dlp_z.schemas.presets import PresetIn, PresetOut
from yt_dlp_z.services import presets

router = APIRouter(prefix="/api/presets", tags=["presets"], dependencies=[Depends(require_auth)])


async def find_preset(db: Db, preset_id: int) -> Preset:
    preset = await presets.get_preset(db, preset_id)
    if preset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Preset not found")
    return preset


async def _save(state: State, db: Db, preset: Preset, body: PresetIn) -> PresetOut:
    await check_user_args(state, body.options, body.extra_args)
    await check_output_dir(state, db, body.output_dir)
    await check_cookie_id(db, body.cookie_id)
    try:
        saved = await presets.save_preset(db, preset, body)
    except presets.DuplicatePresetError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return PresetOut.model_validate(saved)


@router.get("")
async def list_presets(db: Db) -> list[PresetOut]:
    return [PresetOut.model_validate(preset) for preset in await presets.list_presets(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_preset(body: PresetIn, state: State, db: Db) -> PresetOut:
    return await _save(state, db, Preset(), body)


@router.get("/{preset_id}")
async def get_preset(preset_id: int, db: Db) -> PresetOut:
    return PresetOut.model_validate(await find_preset(db, preset_id))


@router.put("/{preset_id}")
async def update_preset(preset_id: int, body: PresetIn, state: State, db: Db) -> PresetOut:
    return await _save(state, db, await find_preset(db, preset_id), body)


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preset(preset_id: int, db: Db) -> None:
    await presets.delete_preset(db, await find_preset(db, preset_id))
