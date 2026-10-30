from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.core.security import hash_password, verify_password
from yt_dlp_z.services.settings_store import get_value, set_values

SETUP_COMPLETE = "setup_complete"
ADMIN_PASSWORD_HASH = "admin_password_hash"  # noqa: S105  (a settings key, not a secret)
SESSION_VERSION = "session_version"
DOWNLOAD_DIR = "download_dir"


async def is_setup_complete(session: AsyncSession) -> bool:
    return await get_value(session, SETUP_COMPLETE) == "true"


async def complete_setup(session: AsyncSession, password: str | None, download_dir: Path) -> None:
    values = {SETUP_COMPLETE: "true", DOWNLOAD_DIR: str(download_dir)}
    if password is not None:
        values[ADMIN_PASSWORD_HASH] = hash_password(password)
    await set_values(session, values)


async def get_download_dir(session: AsyncSession) -> Path | None:
    value = await get_value(session, DOWNLOAD_DIR)
    return Path(value) if value else None


async def check_password(session: AsyncSession, password: str) -> bool:
    password_hash = await get_value(session, ADMIN_PASSWORD_HASH)
    if password_hash is None:
        return False
    return verify_password(password_hash, password)


async def get_session_version(session: AsyncSession) -> int:
    return int(await get_value(session, SESSION_VERSION) or "1")


async def change_password(session: AsyncSession, new_password: str) -> None:
    """Sets a new admin password and invalidates every existing session."""
    next_version = await get_session_version(session) + 1
    await set_values(
        session,
        {ADMIN_PASSWORD_HASH: hash_password(new_password), SESSION_VERSION: str(next_version)},
    )


async def sync_admin_password(session: AsyncSession, password: str) -> None:
    """Makes the stored password match YTDLPZ_ADMIN_PASSWORD. A changed value
    signs out existing sessions; an unchanged one leaves them alone."""
    if await check_password(session, password):
        return
    if await get_value(session, ADMIN_PASSWORD_HASH) is None:
        await set_values(session, {ADMIN_PASSWORD_HASH: hash_password(password)})
        return
    await change_password(session, password)
