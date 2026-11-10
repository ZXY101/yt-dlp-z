"""Telling whether two links point at the same thing, so a client can find a link's jobs.

`watch?v=abc&t=30`, `youtu.be/abc?si=x` and `/shorts/abc` are one video; elsewhere the
address is compared without tracking parameters."""

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse

YOUTUBE_HOSTS = {"youtube.com", "youtu.be", "youtube-nocookie.com"}
VIDEO_PATH_PREFIXES = ("shorts", "live", "embed", "v")
# Parameters that change how a page is shared or opened, not what it shows.
TRACKING_PARAMS = {"si", "feature", "t", "start", "pp", "fbclid", "gclid", "ref", "app"}


def _bare_host(host: str) -> str:
    for prefix in ("www.", "m.", "music."):
        if host.startswith(prefix):
            return host.removeprefix(prefix)
    return host


def _youtube_video_id(host: str, path: str, query: dict[str, str]) -> str | None:
    if host == "youtu.be":
        return path.strip("/").split("/")[0] or None
    if "v" in query:
        return query["v"]
    prefix, _, rest = path.strip("/").partition("/")
    if prefix in VIDEO_PATH_PREFIXES and rest:
        return rest.split("/")[0]
    return None


def _youtube_key(host: str, path: str, query: dict[str, str], whole_playlist: bool) -> str:
    video_id = _youtube_video_id(host, path, query)
    playlist_id = query.get("list")
    if video_id and not (playlist_id and whole_playlist):
        return f"youtube:video:{video_id}"
    if playlist_id:
        return f"youtube:list:{playlist_id}"
    return f"youtube:page:{path.rstrip('/').lower()}"


def link_key(url: str, *, whole_playlist: bool = False) -> str:
    """The same key for links to the same video, playlist or page.

    `whole_playlist` picks the playlist over the video for a video opened from a playlist."""
    parsed = urlparse(url.strip())
    host = _bare_host(parsed.netloc.lower())
    query = dict(parse_qsl(parsed.query))
    if host in YOUTUBE_HOSTS:
        return _youtube_key(host, parsed.path, query, whole_playlist)
    kept = sorted(
        (name, value)
        for name, value in query.items()
        if name not in TRACKING_PARAMS and not name.startswith("utm_")
    )
    suffix = f"?{urlencode(kept)}" if kept else ""
    return f"{host}{parsed.path.rstrip('/')}{suffix}"


def job_link_key(url: str, options: dict[str, Any]) -> str:
    """A job's key: without --no-playlist, yt-dlp downloads the whole playlist."""
    return link_key(url, whole_playlist=not options.get("--no-playlist"))
