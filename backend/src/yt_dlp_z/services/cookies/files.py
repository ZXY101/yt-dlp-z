"""Uploaded cookies files: the DB row (name and summary) plus the file on disk."""

from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.cookie_file import CookieFile
from yt_dlp_z.db.models.preset import Preset
from yt_dlp_z.schemas.cookies import CookieFileUpdate
from yt_dlp_z.services.cookies.parse import summarise_cookies
from yt_dlp_z.services.cookies.store import delete_cookie_file, write_cookie_file
from yt_dlp_z.services.watch.store import unlink_cookie_file


class DuplicateCookieFileError(ValueError):
    pass


async def list_cookie_files(session: AsyncSession) -> Sequence[CookieFile]:
    result = await session.execute(select(CookieFile).order_by(CookieFile.name))
    return result.scalars().all()


async def get_cookie_file(session: AsyncSession, cookie_id: int) -> CookieFile | None:
    return await session.get(CookieFile, cookie_id)


async def save_cookie_file(
    session: AsyncSession, config_dir: Path, cookie_file: CookieFile, values: CookieFileUpdate
) -> CookieFile:
    """Creates or updates a cookies file. Raises CookieFormatError for invalid content."""
    name, content = values.name, values.content
    cookie_file.name = name
    if content is not None:
        summary = summarise_cookies(content)
        cookie_file.cookie_count = summary.cookie_count
        cookie_file.domains = summary.domains
    session.add(cookie_file)
    try:
        await session.flush()
    except IntegrityError as error:
        await session.rollback()
        raise DuplicateCookieFileError(f"A cookies file named {name!r} already exists") from error
    if content is not None:
        write_cookie_file(config_dir, cookie_file.id, content)
    await session.commit()
    await session.refresh(cookie_file)
    return cookie_file


async def delete_cookie_file_entry(
    session: AsyncSession, config_dir: Path, cookie_file: CookieFile
) -> None:
    """Deletes the file and unlinks it from presets and subscriptions.
    Past downloads keep their history."""
    await session.execute(
        update(Preset).where(Preset.cookie_id == cookie_file.id).values(cookie_id=None)
    )
    await unlink_cookie_file(session, cookie_file.id)
    await session.delete(cookie_file)
    await session.commit()
    delete_cookie_file(config_dir, cookie_file.id)
