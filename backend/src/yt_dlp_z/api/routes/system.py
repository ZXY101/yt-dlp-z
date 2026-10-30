import shutil

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from yt_dlp_z.api.deps import State, require_auth
from yt_dlp_z.services.ytdlp.errors import SchemaUnavailableError

router = APIRouter(prefix="/api", tags=["system"], dependencies=[Depends(require_auth)])


class SystemInfo(BaseModel):
    ytdlp_version: str | None
    ytdlp_error: str | None
    ffmpeg_available: bool
    deno_available: bool


@router.get("/system")
async def get_system_info(state: State) -> SystemInfo:
    """Reports missing runtime dependencies so the UI can warn about them."""
    version, error = None, None
    try:
        schema, _ = await state.schemas.get()
        version = schema.ytdlp_version
    except SchemaUnavailableError as exc:
        error = str(exc)
    return SystemInfo(
        ytdlp_version=version,
        ytdlp_error=error,
        ffmpeg_available=shutil.which("ffmpeg") is not None,
        deno_available=shutil.which("deno") is not None,
    )
