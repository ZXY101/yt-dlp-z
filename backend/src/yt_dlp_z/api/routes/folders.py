from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.validation import base_download_dir
from yt_dlp_z.services.folders import suggest_folders
from yt_dlp_z.services.paths import InvalidPathError

router = APIRouter(prefix="/api/folders", tags=["folders"], dependencies=[Depends(require_auth)])


class FolderSuggestions(BaseModel):
    folders: list[str]


@router.get("")
async def list_folders(
    state: State, db: Db, parent: str = Query(default="", max_length=4096)
) -> FolderSuggestions:
    """Sub-folders of `parent` (empty: the default download folder), for autocomplete.
    Only folders inside the allowed download roots are listed; files never are."""
    base_dir = await base_download_dir(db)
    try:
        folders = suggest_folders(parent, base_dir, state.settings.extra_download_roots)
    except InvalidPathError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return FolderSuggestions(folders=folders)
