from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.schemas.ytdlp import YtdlpInfo, YtdlpPreferences
from yt_dlp_z.services import app_settings
from yt_dlp_z.services.ytdlp.updater import UpdateError, UpdateRunningError, bundled_version

router = APIRouter(prefix="/api/ytdlp", tags=["ytdlp"], dependencies=[Depends(require_auth)])

RUNNING = "An update is already running"


async def _info(state: State, db: Db) -> YtdlpInfo:
    updater = state.updater
    # Status first: a "succeeded" status is only set after the new version is in place,
    # so the versions read after it are never older than the status says.
    update = updater.status
    preferences = await app_settings.get_ytdlp_preferences(db)
    return YtdlpInfo(
        **preferences.model_dump(),
        bundled_version=bundled_version(),
        active_version=updater.active_version,
        using_update=updater.using_update,
        update=update,
        latest_version=state.update_checker.latest_version,
        checked_at=state.update_checker.checked_at,
    )


@router.get("")
async def get_ytdlp(state: State, db: Db) -> YtdlpInfo:
    return await _info(state, db)


@router.put("/preferences")
async def set_preferences(body: YtdlpPreferences, state: State, db: Db) -> YtdlpInfo:
    """The channel applies to the next update or check."""
    await app_settings.set_ytdlp_preferences(db, body)
    return await _info(state, db)


@router.post("/check")
async def check_for_update(state: State, db: Db) -> YtdlpInfo:
    """Asks PyPI for the newest version on the chosen channel. Installs nothing."""
    preferences = await app_settings.get_ytdlp_preferences(db)
    try:
        await state.update_checker.check(preferences.channel)
    except UpdateError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    return await _info(state, db)


@router.post("/update", status_code=status.HTTP_202_ACCEPTED)
async def start_update(state: State, db: Db) -> YtdlpInfo:
    """Starts an update in the background; poll GET /api/ytdlp for the result.
    Running downloads keep the version they started with."""
    preferences = await app_settings.get_ytdlp_preferences(db)
    try:
        state.updater.start(preferences.channel)
    except UpdateRunningError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, RUNNING) from error
    return await _info(state, db)


@router.delete("/update")
async def remove_update(state: State, db: Db) -> YtdlpInfo:
    """Goes back to the yt-dlp bundled with the app."""
    try:
        state.updater.reset()
    except UpdateRunningError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, RUNNING) from error
    return await _info(state, db)
