from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.schemas.app_settings import AppSettings
from yt_dlp_z.services import app_settings, auth_service
from yt_dlp_z.services.paths import InvalidPathError, prepare_download_dir

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_auth)])


@router.get("")
async def get_settings(state: State, db: Db) -> AppSettings:
    download_dir = await auth_service.get_download_dir(db)
    if download_dir is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Finish setup first")
    return AppSettings(download_dir=str(download_dir), max_concurrent_downloads=state.jobs.limit)


@router.put("")
async def update_settings(body: AppSettings, state: State, db: Db) -> AppSettings:
    """A new download folder applies to downloads started from now on."""
    try:
        download_dir = prepare_download_dir(body.download_dir)
    except InvalidPathError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    await auth_service.set_download_dir(db, download_dir)
    await app_settings.set_max_concurrent_downloads(db, body.max_concurrent_downloads)
    state.jobs.set_limit(body.max_concurrent_downloads)
    return AppSettings(
        download_dir=str(download_dir), max_concurrent_downloads=body.max_concurrent_downloads
    )
