"""Subscription filters: each check returns why an upload is skipped, or None to keep it."""

import re
from collections.abc import Callable
from datetime import datetime

from yt_dlp_z.schemas.subscriptions import ContentType, SubscriptionFilters
from yt_dlp_z.services.watch.probe import VideoInfo

CONTENT_LABELS = {
    ContentType.VIDEO: "a video",
    ContentType.SHORT: "a Short",
    ContentType.STREAM: "a live stream or premiere",
}


def _content_type(filters: SubscriptionFilters, info: VideoInfo) -> str | None:
    if info.content_type in filters.content_types:
        return None
    return f"It's {CONTENT_LABELS[info.content_type]}"


def _members_only(filters: SubscriptionFilters, info: VideoInfo) -> str | None:
    if info.members_only and not filters.include_members_only:
        return "Members-only"
    return None


def _title(filters: SubscriptionFilters, title: str) -> str | None:
    include, exclude = filters.title_include, filters.title_exclude
    if include and not re.search(include, title, re.IGNORECASE):
        return "The title doesn't match the include filter"
    if exclude and re.search(exclude, title, re.IGNORECASE):
        return "The title matches the exclude filter"
    return None


def _duration(filters: SubscriptionFilters, info: VideoInfo) -> str | None:
    # Upcoming and live streams have no duration yet.
    if info.duration is None:
        return None
    if filters.min_duration is not None and info.duration < filters.min_duration:
        return "Shorter than the minimum duration"
    if filters.max_duration is not None and info.duration > filters.max_duration:
        return "Longer than the maximum duration"
    return None


def _published(filters: SubscriptionFilters, published_at: datetime | None) -> str | None:
    after = filters.published_after
    if after is None or published_at is None:
        return None
    if published_at.date() < after:
        return f"Published before {after.isoformat()}"
    return None


def skip_reason(
    filters: SubscriptionFilters, info: VideoInfo, title: str, published_at: datetime | None
) -> str | None:
    checks: list[Callable[[], str | None]] = [
        lambda: _content_type(filters, info),
        lambda: _members_only(filters, info),
        lambda: _title(filters, title),
        lambda: _duration(filters, info),
        lambda: _published(filters, published_at),
    ]
    for check in checks:
        reason = check()
        if reason is not None:
            return reason
    return None
