import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.routes.job_actions import stop_job
from yt_dlp_z.api.state import AppState
from yt_dlp_z.api.validation import check_cookie_id, check_output_dir
from yt_dlp_z.db.models.job import FINISHED_STATUSES, Job
from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.db.models.video import Video, VideoState
from yt_dlp_z.schemas.subscriptions import (
    DiskUsageOut,
    SubscriptionCreate,
    SubscriptionOut,
    SubscriptionUpdate,
    VideoOut,
    VideoUpdate,
)
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.files import disk_usage
from yt_dlp_z.services.presets import get_preset
from yt_dlp_z.services.watch import store
from yt_dlp_z.services.watch.channel import ChannelError, resolve_channel

router = APIRouter(
    prefix="/api/subscriptions", tags=["subscriptions"], dependencies=[Depends(require_auth)]
)


def to_out(state: AppState, subscription: Subscription) -> SubscriptionOut:
    out = SubscriptionOut.model_validate(subscription)
    out.checking = state.watcher.is_checking(subscription.id)
    return out


async def find_subscription(db: Db, subscription_id: int) -> Subscription:
    subscription = await store.get_subscription(db, subscription_id)
    if subscription is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found")
    return subscription


async def check_references(state: AppState, db: Db, body: SubscriptionUpdate) -> None:
    for preset_id in (body.preset_id, body.stream_preset_id):
        if preset_id is not None and await get_preset(db, preset_id) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "That preset doesn't exist")
    await check_cookie_id(db, body.cookie_id)
    await check_output_dir(state, db, body.output_dir)


@router.get("")
async def list_subscriptions(state: State, db: Db) -> list[SubscriptionOut]:
    return [to_out(state, item) for item in await store.list_subscriptions(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_subscription(body: SubscriptionCreate, state: State, db: Db) -> SubscriptionOut:
    """Resolves the channel, saves it and starts the first check right away."""
    await check_references(state, db, body)
    try:
        await store.check_limit(db)
        channel = await resolve_channel(state.settings.ytdlp_command, body.channel)
        await store.check_not_subscribed(db, channel.channel_id)
    except ChannelError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    except (store.SubscriptionLimitError, store.DuplicateSubscriptionError) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    subscription = await store.create_subscription(db, channel, body)
    if subscription.enabled:
        state.watcher.check_now(subscription.id)
    return to_out(state, subscription)


@router.get("/{subscription_id}")
async def get_subscription(subscription_id: int, state: State, db: Db) -> SubscriptionOut:
    return to_out(state, await find_subscription(db, subscription_id))


@router.put("/{subscription_id}")
async def update_subscription(
    subscription_id: int, body: SubscriptionUpdate, state: State, db: Db
) -> SubscriptionOut:
    subscription = await find_subscription(db, subscription_id)
    await check_references(state, db, body)
    return to_out(state, await store.update_subscription(db, subscription, body))


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(subscription_id: int, db: Db) -> None:
    await store.delete_subscription(db, await find_subscription(db, subscription_id))


@router.post("/{subscription_id}/check", status_code=status.HTTP_202_ACCEPTED)
async def check_subscription(subscription_id: int, state: State, db: Db) -> SubscriptionOut:
    """Starts a check in the background. Poll the subscription to see when it's done."""
    subscription = await find_subscription(db, subscription_id)
    state.watcher.check_now(subscription.id)
    return to_out(state, subscription)


@router.get("/{subscription_id}/videos")
async def list_videos(subscription_id: int, db: Db) -> list[VideoOut]:
    """The 50 most recent videos the subscription has seen, and what happened to each."""
    await find_subscription(db, subscription_id)
    return [
        VideoOut.model_validate(video) for video in await store.list_videos(db, subscription_id)
    ]


IGNORED_REASON = "You chose not to download it"
RECHECK_REASON = "Checked again on the next check"


async def find_video(subscription_id: int, video_id: int, db: Db) -> Video:
    video = await store.get_video(db, subscription_id, video_id)
    if video is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Video not found")
    return video


@router.put("/{subscription_id}/videos/{video_id}")
async def update_video(
    video: Annotated[Video, Depends(find_video)], body: VideoUpdate, state: State, db: Db
) -> VideoOut:
    if body.ignored:
        job = await db.get(Job, video.job_id) if video.job_id is not None else None
        if job is not None and job.status not in FINISHED_STATUSES:
            await stop_job(state, db, job)
        video.state, video.reason = VideoState.IGNORED, IGNORED_REASON
    else:
        # A failed video is looked at again on the next check, filters and all.
        video.state, video.reason = VideoState.FAILED, RECHECK_REASON
    await db.commit()
    return VideoOut.model_validate(video)


# More downloads than this per subscription aren't counted.
USAGE_JOB_LIMIT = 10_000


@router.get("/{subscription_id}/usage")
async def get_disk_usage(subscription_id: int, db: Db) -> DiskUsageOut:
    await find_subscription(db, subscription_id)
    jobs = list(await repository.list_jobs(db, USAGE_JOB_LIMIT, subscription_id))
    usage = await asyncio.to_thread(disk_usage, jobs)
    return DiskUsageOut(downloads=len(jobs), files=usage.files, bytes=usage.bytes)
