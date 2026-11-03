"""Turns what the user typed (a channel URL, @handle or playlist URL) into what a
subscription watches: a YouTube channel id, or a playlist id."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
CHANNEL_ID_PREFIX = "UC"


class ChannelError(ValueError):
    pass


# Mixes are made per viewer and never end; nothing to watch for new videos.
MIX_PREFIX = "RD"


@dataclass(frozen=True)
class Channel:
    channel_id: str  # the playlist id for playlists
    name: str
    url: str
    kind: str = "channel"


def playlist_id_of(url: str) -> str | None:
    """The list= of a playlist link, or of a video opened from a playlist."""
    values = parse_qs(urlparse(url).query).get("list")
    return values[0] if values else None


def channel_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("@"):
        return f"https://www.youtube.com/{raw}"
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in YOUTUBE_HOSTS:
        raise ChannelError("Enter a YouTube channel or playlist URL, or @handle")
    return raw


def _channel_id(data: dict[str, Any]) -> str | None:
    for key in ("channel_id", "id"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith(CHANNEL_ID_PREFIX):
            return value
    return None


def _text(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def channel_from_info(data: dict[str, Any]) -> Channel:
    channel_id = _channel_id(data)
    if channel_id is None:
        raise ChannelError("That address isn't a YouTube channel")
    name = _text(data, "channel", "uploader", "title") or channel_id
    url = _text(data, "channel_url") or f"https://www.youtube.com/channel/{channel_id}"
    return Channel(channel_id=channel_id, name=name, url=url)


async def _resolve_playlist(ytdlp_command: list[str], playlist_id: str) -> Channel:
    if playlist_id.startswith(MIX_PREFIX):
        raise ChannelError("Mixes can't be watched: they're made for each viewer and never end")
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    try:
        data = await run_ytdlp_json(ytdlp_command, ["--flat-playlist", "--playlist-end", "1"], url)
    except YtdlpJsonError as error:
        raise ChannelError(f"Couldn't open that playlist: {error}") from error
    name = _text(data, "title") or playlist_id
    return Channel(channel_id=playlist_id, name=name, url=url, kind="playlist")


async def resolve_channel(ytdlp_command: list[str], raw: str) -> Channel:
    url = channel_url(raw)
    playlist_id = playlist_id_of(url)
    if playlist_id is not None:
        return await _resolve_playlist(ytdlp_command, playlist_id)
    # One flat entry is enough: the channel fields sit on the playlist itself.
    args = ["--flat-playlist", "--playlist-end", "1"]
    try:
        data = await run_ytdlp_json(ytdlp_command, args, url)
    except YtdlpJsonError as error:
        raise ChannelError(f"Couldn't open that channel: {error}") from error
    return channel_from_info(data)
