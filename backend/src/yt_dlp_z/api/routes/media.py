import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.validation import check_cookie_id
from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import utcnow
from yt_dlp_z.schemas.media import MediaInfo, MediaProbeRequest
from yt_dlp_z.services import app_settings
from yt_dlp_z.services.cookies.store import working_copy
from yt_dlp_z.services.watch.probe import MEMBERS_ERROR_HINT
from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError
from yt_dlp_z.services.ytdlp.media import media_info, probe_media

router = APIRouter(prefix="/api/media", tags=["media"], dependencies=[Depends(require_auth)])

# yt-dlp prefixes errors with the extractor and video id: "[youtube] dQw4w9WgXcQ: …".
ERROR_PREFIX = re.compile(r"^\[[^\]]+\]\s*(?:[^:\s]+:\s+)?")
MEMBERS_MESSAGE = "This is for channel members only. Choose a cookies file from a member's account."


@contextmanager
def _cookies(settings: Settings, cookie_id: int | None) -> Iterator[Path | None]:
    if cookie_id is None:
        yield None
        return
    with working_copy(settings.config_dir, cookie_id, f"probe-{uuid4().hex}") as path:
        yield path


def _probe_failed(error: YtdlpJsonError, *, with_cookies: bool) -> HTTPException:
    message = ERROR_PREFIX.sub("", str(error))
    if MEMBERS_ERROR_HINT in message.lower() and not with_cookies:
        message = MEMBERS_MESSAGE
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, message)


@router.post("/probe")
async def probe(body: MediaProbeRequest, state: State, db: Db) -> MediaInfo:
    """Asks yt-dlp what the link is, so the form can catch bad links and offer the right
    choices (playlist, recording) before anything is queued."""
    await check_cookie_id(db, body.cookie_id)
    settings = state.settings
    try:
        with _cookies(settings, body.cookie_id) as cookies:
            data = await probe_media(
                settings.ytdlp_command, body.url, cookies=cookies, no_playlist=body.no_playlist
            )
    except YtdlpJsonError as error:
        raise _probe_failed(error, with_cookies=body.cookie_id is not None) from error
    recording = await app_settings.get_recording_settings(db)
    return media_info(data, recording, utcnow())
