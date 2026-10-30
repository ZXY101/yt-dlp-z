from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.db.models.cookie_file import CookieFile
from yt_dlp_z.schemas.cookies import (
    CookieCheckRequest,
    CookieCheckResult,
    CookieFileCreate,
    CookieFileOut,
    CookieFileUpdate,
)
from yt_dlp_z.services.cookies import files
from yt_dlp_z.services.cookies.check import check_cookies
from yt_dlp_z.services.cookies.parse import CookieFormatError
from yt_dlp_z.services.cookies.store import working_copy

router = APIRouter(prefix="/api/cookies", tags=["cookies"], dependencies=[Depends(require_auth)])


async def find_cookie_file(db: Db, cookie_id: int) -> CookieFile:
    cookie_file = await files.get_cookie_file(db, cookie_id)
    if cookie_file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cookies file not found")
    return cookie_file


async def _save(
    state: State, db: Db, cookie_file: CookieFile, body: CookieFileUpdate
) -> CookieFileOut:
    try:
        saved = await files.save_cookie_file(db, state.settings.config_dir, cookie_file, body)
    except CookieFormatError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except files.DuplicateCookieFileError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return CookieFileOut.model_validate(saved)


@router.get("")
async def list_cookie_files(db: Db) -> list[CookieFileOut]:
    return [CookieFileOut.model_validate(item) for item in await files.list_cookie_files(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_cookie_file(body: CookieFileCreate, state: State, db: Db) -> CookieFileOut:
    return await _save(state, db, CookieFile(), body)


@router.put("/{cookie_id}")
async def update_cookie_file(
    cookie_id: int, body: CookieFileUpdate, state: State, db: Db
) -> CookieFileOut:
    cookie_file = await find_cookie_file(db, cookie_id)
    return await _save(state, db, cookie_file, body)


@router.delete("/{cookie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cookie_file(cookie_id: int, state: State, db: Db) -> None:
    cookie_file = await find_cookie_file(db, cookie_id)
    await files.delete_cookie_file_entry(db, state.settings.config_dir, cookie_file)


@router.post("/{cookie_id}/check")
async def check_cookie_file(
    cookie_id: int, body: CookieCheckRequest, state: State, db: Db
) -> CookieCheckResult:
    """Opens one page with these cookies, to see whether they still sign in."""
    await find_cookie_file(db, cookie_id)
    settings = state.settings
    with working_copy(settings.config_dir, cookie_id, f"check-{uuid4().hex}") as path:
        return await check_cookies(settings.ytdlp_command, path, body.url)
