"""Asks yt-dlp what a link points at before it is downloaded (the download form's check)."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from yt_dlp_z.schemas.media import MediaInfo, MediaKind
from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json

# Playlist entries listed by the check. Listing a whole channel can take minutes.
ENTRY_LIMIT = 50
MEMBERS_ONLY = {"subscriber_only", "premium_only"}
LIVE_KINDS: dict[str, MediaKind] = {"is_live": "live", "is_upcoming": "upcoming"}
# yt-dlp's errors for streams and premieres that haven't started ("This live event will
# begin in 3 hours", "Premieres in 2 days").
UPCOMING_HINTS = ("will begin", "premieres in")


def probe_args(*, cookies: Path | None, no_playlist: bool) -> list[str]:
    args = ["--flat-playlist", "--playlist-items", f"1:{ENTRY_LIMIT}"]
    if no_playlist:
        args.append("--no-playlist")
    if cookies is not None:
        args += ["--cookies", str(cookies)]
    return args


# YouTube only (other sites ignore it): one lightweight player and no JS challenge, about
# 2 s instead of 6 for a video. That player can't use cookies, and YouTube changes which
# players work, so anything it can't answer goes through the full check.
FAST_ARGS = ["--extractor-args", "youtube:player_skip=js;player_client=android_vr"]


async def _run_probe(ytdlp_command: list[str], args: list[str], url: str) -> dict[str, Any]:
    try:
        return await run_ytdlp_json(ytdlp_command, args, url)
    except YtdlpJsonError as error:
        if not any(hint in str(error).lower() for hint in UPCOMING_HINTS):
            raise
    # Upcoming streams have no formats yet, so yt-dlp needs this to report their start
    # time. Only used for them: it also turns real failures (unavailable videos, ended
    # streams) into empty results that look fine.
    return await run_ytdlp_json(ytdlp_command, [*args, "--ignore-no-formats-error"], url)


async def probe_media(
    ytdlp_command: list[str], url: str, *, cookies: Path | None, no_playlist: bool
) -> dict[str, Any]:
    args = probe_args(cookies=cookies, no_playlist=no_playlist)
    if cookies is None:
        try:
            return await _run_probe(ytdlp_command, [*args, *FAST_ARGS], url)
        except YtdlpJsonError:
            pass  # The full check below gives the real answer, or the real error.
    return await _run_probe(ytdlp_command, args, url)


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


def _area(thumbnail: dict[str, Any]) -> int:
    return (_number(thumbnail.get("width")) or 0) * (_number(thumbnail.get("height")) or 0)


def _thumbnail(data: dict[str, Any]) -> str | None:
    if thumbnail := _text(data, "thumbnail"):
        return thumbnail
    # Playlists and channels list several; entries without a size (a channel's
    # "avatar_uncropped") may not display, so the largest sized one wins.
    thumbnails = [t for t in data.get("thumbnails") or [] if isinstance(t, dict)]
    usable = [t for t in thumbnails if isinstance(t.get("url"), str)]
    if not usable:
        return None
    return str(max(usable, key=_area)["url"])


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


def media_info(data: dict[str, Any]) -> MediaInfo:
    kind = _kind(data)
    release = _timestamp(data.get("release_timestamp"))
    return MediaInfo(
        kind=kind,
        title=_text(data, "title"),
        uploader=_text(data, "uploader", "channel", "playlist_uploader"),
        thumbnail=_thumbnail(data),
        site=_text(data, "webpage_url_domain", "extractor_key"),
        duration=_number(data.get("duration")),
        entry_count=_entry_count(data) if kind in {"playlist", "channel"} else None,
        starts_at=release if kind == "upcoming" else None,
        live_since=release if kind == "live" else None,
        members_only=data.get("availability") in MEMBERS_ONLY,
    )
