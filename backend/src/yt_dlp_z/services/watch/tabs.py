"""Channel tabs (/videos, /streams) listed with yt-dlp: the newest entries, no dates."""

import logging
from typing import Any

from yt_dlp_z.services.watch.feed import FeedEntry, FeedError, feed_url, fetch_feed
from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json

logger = logging.getLogger(__name__)

# What the RSS feed lists: the newest 15 uploads.
FEED_SIZE = 15


def _entry(data: Any) -> FeedEntry | None:
    if not isinstance(data, dict) or not isinstance(data.get("id"), str):
        return None
    title = data.get("title")
    return FeedEntry(
        video_id=data["id"],
        title=title if isinstance(title, str) else data["id"],
        published_at=None,
    )


async def fetch_tab(
    ytdlp_command: list[str], channel_id: str, tab: str, count: int
) -> list[FeedEntry]:
    """Newest first. Raises YtdlpJsonError when yt-dlp fails."""
    url = f"https://www.youtube.com/channel/{channel_id}/{tab}"
    args = ["--flat-playlist", "--playlist-end", str(count)]
    data = await run_ytdlp_json(ytdlp_command, args, url)
    entries = [_entry(item) for item in data.get("entries") or []]
    return [entry for entry in entries if entry is not None]


async def latest_uploads(
    feed_template: str, ytdlp_command: list[str], channel_id: str
) -> list[FeedEntry]:
    """The RSS feed, else the videos tab. YouTube's feeds go down for days at times
    (404 for every channel); the tab costs a yt-dlp run but keeps the channel watched.
    Raises FeedError when both fail."""
    try:
        return await fetch_feed(feed_url(feed_template, channel_id))
    except FeedError as feed_error:
        try:
            entries = await fetch_tab(ytdlp_command, channel_id, "videos", FEED_SIZE)
        except YtdlpJsonError as tab_error:
            raise FeedError(f"{feed_error} The videos tab failed too: {tab_error}") from tab_error
        logger.warning("Read the videos tab of %s instead of its feed: %s", channel_id, feed_error)
        return entries


# Playlists longer than this are only read this far.
PLAYLIST_LIMIT = 1000
# A channel's "Uploads" playlist lists the newest first, unlike playlists people make.
UPLOADS_PREFIX = "UU"


async def playlist_entries(ytdlp_command: list[str], playlist_id: str) -> list[FeedEntry]:
    """The playlist's videos, newest first. Playlists people make add new videos at the
    end, so their last ones come first. Raises FeedError when yt-dlp fails."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    args = ["--flat-playlist", "--playlist-end", str(PLAYLIST_LIMIT)]
    try:
        data = await run_ytdlp_json(ytdlp_command, args, url)
    except YtdlpJsonError as error:
        raise FeedError(f"Couldn't read the playlist: {error}") from error
    entries = [_entry(item) for item in data.get("entries") or []]
    found = [entry for entry in entries if entry is not None]
    return found if playlist_id.startswith(UPLOADS_PREFIX) else found[::-1]
