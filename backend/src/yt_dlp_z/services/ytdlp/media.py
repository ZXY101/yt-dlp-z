"""Asks yt-dlp what a link points at before it is downloaded (the download form's check)."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from yt_dlp_z.schemas.app_settings import RecordingSettings
from yt_dlp_z.schemas.media import MediaInfo, MediaKind
from yt_dlp_z.services.live.plan import plan_recording
from yt_dlp_z.services.ytdlp.json_run import run_ytdlp_json

# Playlist entries listed by the check. Listing a whole channel can take minutes.
ENTRY_LIMIT = 50
MEMBERS_ONLY = {"subscriber_only", "premium_only"}
LIVE_KINDS: dict[str, MediaKind] = {"is_live": "live", "is_upcoming": "upcoming"}


def probe_args(*, cookies: Path | None, no_playlist: bool) -> list[str]:
    # Upcoming streams have no formats yet; without --ignore-no-formats-error yt-dlp
    # fails on them instead of reporting their start time.
    args = ["--flat-playlist", "--playlist-items", f"1:{ENTRY_LIMIT}", "--ignore-no-formats-error"]
    if no_playlist:
        args.append("--no-playlist")
    if cookies is not None:
        args += ["--cookies", str(cookies)]
    return args


async def probe_media(
    ytdlp_command: list[str], url: str, *, cookies: Path | None, no_playlist: bool
) -> dict[str, Any]:
    args = probe_args(cookies=cookies, no_playlist=no_playlist)
    return await run_ytdlp_json(ytdlp_command, args, url)


def _text(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _number(value: object) -> int | None:
    return int(value) if isinstance(value, int | float) else None


def _timestamp(value: object) -> datetime | None:
    seconds = _number(value)
    return datetime.fromtimestamp(seconds, UTC) if seconds is not None else None


def _thumbnail(data: dict[str, Any]) -> str | None:
    if thumbnail := _text(data, "thumbnail"):
        return thumbnail
    # Playlists list several sizes, smallest first.
    thumbnails = [t for t in data.get("thumbnails") or [] if isinstance(t, dict)]
    urls = [t["url"] for t in thumbnails if isinstance(t.get("url"), str)]
    return urls[-1] if urls else None


def _entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [entry for entry in data.get("entries") or [] if isinstance(entry, dict)]


def _kind(data: dict[str, Any]) -> MediaKind:
    if data.get("_type") != "playlist":
        return LIVE_KINDS.get(str(data.get("live_status")), "video")
    entries = _entries(data)
    if entries and all(entry.get("_type") == "playlist" for entry in entries):
        return "channel"
    return "playlist"


def _entry_count(data: dict[str, Any]) -> int | None:
    if count := _number(data.get("playlist_count")):
        return count
    listed = len(_entries(data))
    # A full page of entries means there may be more than were listed.
    return listed if listed < ENTRY_LIMIT else None


def media_info(data: dict[str, Any], recording: RecordingSettings, now: datetime) -> MediaInfo:
    kind = _kind(data)
    release = _timestamp(data.get("release_timestamp"))
    live_since = release if kind == "live" else None
    from_start = None
    if kind in {"live", "upcoming"}:
        from_start = plan_recording(recording, live_since, now).record_from_start
    return MediaInfo(
        kind=kind,
        title=_text(data, "title"),
        uploader=_text(data, "uploader", "channel", "playlist_uploader"),
        thumbnail=_thumbnail(data),
        site=_text(data, "extractor_key"),
        duration=_number(data.get("duration")),
        entry_count=_entry_count(data) if kind in {"playlist", "channel"} else None,
        starts_at=release if kind == "upcoming" else None,
        live_since=live_since,
        members_only=data.get("availability") in MEMBERS_ONLY,
        record_from_start=from_start,
    )
