"""Endpoints for the E2E suite. Only mounted when YTDLPZ_TEST_MODE is set."""

import shutil
from typing import Any
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import delete

from yt_dlp_z.api.deps import Db, State
from yt_dlp_z.db.base import Base
from yt_dlp_z.services.auth_service import sync_admin_password
from yt_dlp_z.services.notify.store import NtfyConfig

router = APIRouter(prefix="/api/test", tags=["testing"], include_in_schema=False)

# Fake channel feeds, served to the subscription poller (YTDLPZ_YOUTUBE_FEED_URL).
_feeds: dict[str, str] = {}
# Messages posted to the fake ntfy server below.
_ntfy: list[dict[str, Any]] = []


class FakeFeedEntry(BaseModel):
    video_id: str
    title: str
    published: str = "2026-01-01T00:00:00+00:00"


def _atom(entries: list[FakeFeedEntry]) -> str:
    items = "".join(
        f"<entry><yt:videoId>{escape(entry.video_id)}</yt:videoId>"
        f"<title>{escape(entry.title)}</title>"
        f"<published>{escape(entry.published)}</published></entry>"
        for entry in entries
    )
    return (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        f'xmlns:yt="http://www.youtube.com/xml/schemas/2015">{items}</feed>'
    )


@router.put("/feeds/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def set_feed(channel_id: str, entries: list[FakeFeedEntry]) -> None:
    """Entries newest first, like YouTube's feed."""
    _feeds[channel_id] = _atom(entries)


@router.get("/feeds/{channel_id}")
async def get_feed(channel_id: str) -> Response:
    if channel_id not in _feeds:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such feed")
    return Response(_feeds[channel_id], media_type="application/atom+xml")


@router.post("/ntfy", status_code=status.HTTP_204_NO_CONTENT)
async def receive_ntfy(message: dict[str, Any]) -> None:
    """A stand-in ntfy server: set the server to <app>/api/test/ntfy."""
    _ntfy.append(message)


@router.get("/ntfy")
async def ntfy_messages() -> list[dict[str, Any]]:
    return _ntfy


@router.get("/pot/ping")
async def pot_ping() -> dict[str, Any]:
    """A stand-in bgutil PO token server: set the provider to <app>/api/test/pot."""
    return {"server_uptime": 1.0, "version": "2.0.2"}


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset(state: State, db: Db) -> None:
    await state.watcher.stop_checks()
    await state.jobs.stop_all()
    _feeds.clear()
    _ntfy.clear()
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(delete(table))
    await db.commit()
    for folder in ("logs", "cookies"):
        shutil.rmtree(state.settings.config_dir / folder, ignore_errors=True)
    state.login_limiter.reset()
    state.probes.clear()
    state.notifier.config = NtfyConfig()
    await state.pot.configure(None)
    state.jobs.downloads.set_limit(state.settings.max_concurrent_downloads)
    state.jobs.recordings.set_limit(state.settings.max_concurrent_recordings)
    # Mirror a fresh start, which applies YTDLPZ_ADMIN_PASSWORD.
    if state.settings.admin_password is not None:
        await sync_admin_password(db, state.settings.admin_password.get_secret_value())
