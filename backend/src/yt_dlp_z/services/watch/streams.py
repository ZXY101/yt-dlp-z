"""Backup sweep of a channel's /streams tab. The RSS feed sometimes misses scheduled and
live streams; this catches them. It costs a yt-dlp run, so it runs at most every 30 min."""

import logging
from datetime import datetime, timedelta

from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.schemas.subscriptions import ContentType, SubscriptionFilters
from yt_dlp_z.services.watch.feed import FeedEntry
from yt_dlp_z.services.watch.tabs import fetch_tab
from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError

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


async def fetch_stream_entries(ytdlp_command: list[str], channel_id: str) -> list[FeedEntry]:
    """The newest entries of the streams tab, or none when yt-dlp fails (the RSS feed
    still covers most streams, so a failed sweep shouldn't fail the whole check)."""
    try:
        return await fetch_tab(ytdlp_command, channel_id, "streams", SWEEP_ENTRIES)
    except YtdlpJsonError as error:
        logger.warning("Couldn't read the streams tab of %s: %s", channel_id, error)
        return []
