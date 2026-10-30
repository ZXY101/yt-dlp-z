from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.schemas.ytdlp import YtdlpChannelBody, YtdlpInfo
from yt_dlp_z.services import app_settings
from yt_dlp_z.services.ytdlp.updater import UpdateRunningError, bundled_version

router = APIRouter(prefix="/api/ytdlp", tags=["ytdlp"], dependencies=[Depends(require_auth)])

RUNNING = "An update is already running"


async def _info(state: State, db: Db) -> YtdlpInfo:
    updater = state.updater
    # Status first: a "succeeded" status is only set after the new version is in place,
    # so the versions read after it are never older than the status says.
    update = updater.status
    return YtdlpInfo(
        bundled_version=bundled_version(),
        active_version=updater.active_version,
        using_update=updater.using_update,
        channel=await app_settings.get_ytdlp_channel(db),
        update=update,
    )


@router.get("")
async def get_ytdlp(state: State, db: Db) -> YtdlpInfo:
    return await _info(state, db)


@router.put("/channel")
async def set_channel(body: YtdlpChannelBody, state: State, db: Db) -> YtdlpInfo:
    """Applies to the next update."""
    await app_settings.set_ytdlp_channel(db, body.channel)
    return await _info(state, db)


@router.post("/update", status_code=status.HTTP_202_ACCEPTED)
async def start_update(state: State, db: Db) -> YtdlpInfo:
    """Starts an update in the background; poll GET /api/ytdlp for the result.
    Running downloads keep the version they started with."""
    try:
        state.updater.start(await app_settings.get_ytdlp_channel(db))
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
