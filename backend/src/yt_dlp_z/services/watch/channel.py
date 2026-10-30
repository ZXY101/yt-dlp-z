"""Turns what the user typed (a channel URL or @handle) into a YouTube channel id."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
CHANNEL_ID_PREFIX = "UC"


class ChannelError(ValueError):
    pass


@dataclass(frozen=True)
class Channel:
    channel_id: str
    name: str
    url: str


def channel_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("@"):
        return f"https://www.youtube.com/{raw}"
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in YOUTUBE_HOSTS:
        raise ChannelError("Enter a YouTube channel URL or @handle")
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


async def resolve_channel(ytdlp_command: list[str], raw: str) -> Channel:
    url = channel_url(raw)
    # One flat entry is enough: the channel fields sit on the playlist itself.
    args = ["--flat-playlist", "--playlist-end", "1"]
    try:
        data = await run_ytdlp_json(ytdlp_command, args, url)
    except YtdlpJsonError as error:
        raise ChannelError(f"Couldn't open that channel: {error}") from error
    return channel_from_info(data)
