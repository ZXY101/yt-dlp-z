"""Backup sweep of a channel's /streams tab. The RSS feed sometimes misses scheduled and
live streams; this catches them. It costs a yt-dlp run, so it runs at most every 30 min."""

import logging
from datetime import datetime, timedelta
from typing import Any

from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.schemas.subscriptions import ContentType, SubscriptionFilters
from yt_dlp_z.services.watch.feed import FeedEntry
from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json

logger = logging.getLogger(__name__)

SWEEP_INTERVAL = timedelta(minutes=30)
# Live and upcoming streams sit at the top of the tab.
SWEEP_ENTRIES = 10


def sweep_due(subscription: Subscription, now: datetime) -> bool:
    filters = SubscriptionFilters.model_validate(subscription.filters)
    if ContentType.STREAM not in filters.content_types:
        return False
    last = subscription.streams_checked_at
    if last is None:
        return True
    if last.tzinfo is None:  # SQLite drops the timezone; stored values are UTC.
        last = last.replace(tzinfo=now.tzinfo)
    return now >= last + SWEEP_INTERVAL


def _entry(data: Any) -> FeedEntry | None:
    if not isinstance(data, dict) or not isinstance(data.get("id"), str):
        return None
    title = data.get("title")
    return FeedEntry(
        video_id=data["id"],
        title=title if isinstance(title, str) else data["id"],
        published_at=None,
    )


async def fetch_stream_entries(ytdlp_command: list[str], channel_id: str) -> list[FeedEntry]:
    """The newest entries of the streams tab, or none when yt-dlp fails (the RSS feed
    still covers most streams, so a failed sweep shouldn't fail the whole check)."""
    url = f"https://www.youtube.com/channel/{channel_id}/streams"
    args = ["--flat-playlist", "--playlist-end", str(SWEEP_ENTRIES)]
    try:
        data = await run_ytdlp_json(ytdlp_command, args, url)
    except YtdlpJsonError as error:
        logger.warning("Couldn't read the streams tab of %s: %s", channel_id, error)
        return []
    entries = [_entry(item) for item in data.get("entries") or []]
    return [entry for entry in entries if entry is not None]
