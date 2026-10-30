"""One check of one subscription: read the feed, then probe, filter and queue new videos."""

import contextlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import utcnow
from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.db.models.video import Video, VideoState
from yt_dlp_z.schemas.subscriptions import SubscriptionFilters
from yt_dlp_z.services.cookies.store import working_copy
from yt_dlp_z.services.watch.enqueue import (
    EnqueueError,
    WatchContext,
    effective_cookie_id,
    enqueue_video,
    preset_for,
)
from yt_dlp_z.services.watch.feed import FeedEntry, FeedError, feed_url, fetch_feed
from yt_dlp_z.services.watch.filters import skip_reason
from yt_dlp_z.services.watch.probe import ProbeError, VideoInfo, probe_video

BEFORE_SUBSCRIBING = "Uploaded before you subscribed"
LIVE_STATES = {"is_upcoming": VideoState.UPCOMING, "is_live": VideoState.LIVE}


async def check_subscription(context: WatchContext, subscription_id: int) -> None:
    async with context.session_factory() as session:
        subscription = await session.get(Subscription, subscription_id)
        if subscription is None:
            return
        url = feed_url(context.settings.youtube_feed_url, subscription.channel_id)
        try:
            entries = await fetch_feed(url)
        except FeedError as error:
            subscription.last_error = str(error)
            await session.commit()
            return
        await _handle_entries(context, session, subscription, entries)
        subscription.last_checked_at = utcnow()
        subscription.last_error = None
        await session.commit()


async def _known_videos(session: AsyncSession, subscription_id: int) -> dict[str, Video]:
    result = await session.execute(select(Video).where(Video.subscription_id == subscription_id))
    return {video.video_id: video for video in result.scalars()}


def _needs_work(known: dict[str, Video], entry: FeedEntry) -> bool:
    """New videos, and ones whose last probe failed (retried on every check)."""
    video = known.get(entry.video_id)
    return video is None or video.state == VideoState.FAILED


async def _handle_entries(
    context: WatchContext,
    session: AsyncSession,
    subscription: Subscription,
    entries: list[FeedEntry],
) -> None:
    known = await _known_videos(session, subscription.id)
    first_check = subscription.last_checked_at is None
    pending = [entry for entry in entries if _needs_work(known, entry)]
    with contextlib.ExitStack() as cleanup:
        cookies = await _probe_cookies(context, session, subscription, cleanup)
        run = EntryHandler(context, session, subscription, cookies)
        for index, entry in enumerate(pending):
            video = known.get(entry.video_id) or Video(
                subscription_id=subscription.id,
                video_id=entry.video_id,
                title=entry.title,
                published_at=entry.published_at,
            )
            if first_check and index >= subscription.backfill:
                _set_state(video, VideoState.SKIPPED, BEFORE_SUBSCRIBING)
            else:
                await run.handle(video)
            # Added only now: a half-filled row must not be autoflushed mid-handling.
            session.add(video)
            await session.commit()


async def _probe_cookies(
    context: WatchContext,
    session: AsyncSession,
    subscription: Subscription,
    cleanup: contextlib.ExitStack,
) -> Path | None:
    """A private copy of the cookies the downloads will use, so the probe sees the same."""
    cookie_id = effective_cookie_id(subscription, await preset_for(session, subscription))
    if cookie_id is None:
        return None
    config_dir = context.settings.config_dir
    owner = f"watch-{subscription.id}"
    try:
        return cleanup.enter_context(working_copy(config_dir, cookie_id, owner))
    except FileNotFoundError:
        # Deleted since; the probe runs without cookies and the download reports it.
        return None


def _set_state(video: Video, state: VideoState, reason: str | None = None) -> None:
    video.state = state
    video.reason = reason


class EntryHandler:
    """Decides what happens to one new video: skip, wait for its stream, or download."""

    def __init__(
        self,
        context: WatchContext,
        session: AsyncSession,
        subscription: Subscription,
        cookies: Path | None,
    ) -> None:
        self._context = context
        self._session = session
        self._subscription = subscription
        self._cookies = cookies
        self._filters = SubscriptionFilters.model_validate(subscription.filters)

    async def handle(self, video: Video) -> None:
        ytdlp_command = self._context.settings.ytdlp_command
        try:
            info = await probe_video(ytdlp_command, video.video_id, self._cookies)
        except ProbeError as error:
            if error.members_only and not self._filters.include_members_only:
                _set_state(video, VideoState.SKIPPED, "Members-only")
            else:
                _set_state(video, VideoState.FAILED, str(error))
            return
        _record_info(video, info)
        reason = skip_reason(self._filters, info, video.title, video.published_at)
        if reason is not None:
            _set_state(video, VideoState.SKIPPED, reason)
            return
        live_state = LIVE_STATES.get(info.live_status or "")
        if live_state is not None:
            # Recording upcoming and live streams arrives with milestone 5.
            _set_state(video, live_state)
            return
        await self._download(video)

    async def _download(self, video: Video) -> None:
        context, session, subscription = self._context, self._session, self._subscription
        try:
            job = await enqueue_video(context, session, subscription, video.video_id)
        except EnqueueError as error:
            _set_state(video, VideoState.FAILED, str(error))
            return
        video.job_id = job.id
        _set_state(video, VideoState.QUEUED)


def _record_info(video: Video, info: VideoInfo) -> None:
    video.title = info.title or video.title
    video.live_status = info.live_status
    video.release_at = info.release_at
