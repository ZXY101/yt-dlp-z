"""Checks shared by routes that accept yt-dlp options and folders (jobs, presets)."""

from collections.abc import Mapping
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.api.state import AppState
from yt_dlp_z.schemas.jobs import OptionValue
from yt_dlp_z.services import auth_service
from yt_dlp_z.services.paths import InvalidPathError, check_job_dir, resolve_job_dir
from yt_dlp_z.services.ytdlp.args import build_user_args
from yt_dlp_z.services.ytdlp.errors import ArgumentError, SchemaUnavailableError


async def check_user_args(
    state: AppState, options: Mapping[str, OptionValue], extra_args: str
) -> None:
    """Rejects bad options up front so the user sees the problem immediately."""
    try:
        _, index = await state.schemas.get()
    except SchemaUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    try:
        allow_unsafe = state.settings.allow_unsafe_options
        build_user_args(index, options, extra_args, allow_unsafe=allow_unsafe)
    except ArgumentError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error


async def _base_dir(db: AsyncSession) -> Path:
    base_dir = await auth_service.get_download_dir(db)
    if base_dir is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Finish setup first")
    return base_dir


async def output_dir_for_job(state: AppState, db: AsyncSession, requested: str | None) -> Path:
    """The checked download folder for a new job, created if needed."""
    base_dir = await _base_dir(db)
    try:
        return resolve_job_dir(requested, base_dir, state.settings.extra_download_roots)
    except InvalidPathError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error


async def check_output_dir(state: AppState, db: AsyncSession, requested: str | None) -> None:
    """Checks a folder that is stored for later use (presets) without creating it."""
    base_dir = await _base_dir(db)
    try:
        check_job_dir(requested, base_dir, state.settings.extra_download_roots)
    except InvalidPathError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
