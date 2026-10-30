"""Asks yt-dlp what a new feed entry is (video, Short, stream) before filtering it."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from yt_dlp_z.schemas.subscriptions import ContentType
from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json

STREAM_STATUSES = {"is_live", "is_upcoming", "was_live", "post_live"}
MEMBERS_ONLY = {"subscriber_only", "premium_only"}
# yt-dlp's error text when a members-only video is opened without a member's cookies.
MEMBERS_ERROR_HINT = "members"


class ProbeError(Exception):
    def __init__(self, message: str, members_only: bool) -> None:
        super().__init__(message)
        self.members_only = members_only


@dataclass(frozen=True)
class VideoInfo:
    title: str | None
    content_type: ContentType
    live_status: str | None
    duration: int | None
    release_at: datetime | None
    members_only: bool


def video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _content_type(data: dict[str, Any]) -> ContentType:
    if data.get("live_status") in STREAM_STATUSES:
        return ContentType.STREAM
    media_type = data.get("media_type")
    url = str(data.get("webpage_url") or "")
    if media_type == "short" or "/shorts/" in url:
        return ContentType.SHORT
    return ContentType.VIDEO


def _optional_int(value: object) -> int | None:
    return int(value) if isinstance(value, int | float) else None


def info_from_json(data: dict[str, Any]) -> VideoInfo:
    release = _optional_int(data.get("release_timestamp"))
    title = data.get("title")
    return VideoInfo(
        title=title if isinstance(title, str) else None,
        content_type=_content_type(data),
        live_status=data.get("live_status"),
        duration=_optional_int(data.get("duration")),
        release_at=datetime.fromtimestamp(release, UTC) if release is not None else None,
        members_only=data.get("availability") in MEMBERS_ONLY,
    )


async def probe_video(ytdlp_command: list[str], video_id: str, cookies: Path | None) -> VideoInfo:
    # Upcoming streams have no formats yet; without this yt-dlp fails on them
    # ("This live event will begin in …") instead of reporting their start time.
    args = ["--no-playlist", "--ignore-no-formats-error"]
    if cookies is not None:
        args += ["--cookies", str(cookies)]
    try:
        data = await run_ytdlp_json(ytdlp_command, args, video_url(video_id))
    except YtdlpJsonError as error:
        members_only = MEMBERS_ERROR_HINT in str(error).lower()
        raise ProbeError(str(error), members_only=members_only) from error
    return info_from_json(data)
