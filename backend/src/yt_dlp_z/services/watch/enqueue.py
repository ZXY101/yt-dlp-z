"""Creates the download or recording job for a subscription's new video, using its preset."""

import dataclasses
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import Job, JobKind, JobStatus, utcnow
from yt_dlp_z.db.models.preset import Preset
from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.db.models.video import Video
from yt_dlp_z.services import auth_service
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.jobs.context import job_log_path, publish_job
from yt_dlp_z.services.jobs.queues import JobQueues
from yt_dlp_z.services.live.plan import RecordingPlan, plan_recording
from yt_dlp_z.services.live.scheduler import recording_status
from yt_dlp_z.services.paths import InvalidPathError, resolve_job_dir
from yt_dlp_z.services.presets import default_recording, preset_recording
from yt_dlp_z.services.watch.probe import video_url


@dataclass(frozen=True)
class WatchContext:
    session_factory: async_sessionmaker[AsyncSession]
    settings: Settings
    hub: EventHub
    jobs: JobQueues


class EnqueueError(Exception):
    pass


async def _get_preset(session: AsyncSession, preset_id: int | None) -> Preset | None:
    return None if preset_id is None else await session.get(Preset, preset_id)


async def preset_for(
    session: AsyncSession, subscription: Subscription, *, stream: bool = False
) -> Preset | None:
    """Streams use the subscription's stream preset when it has one."""
    if stream and subscription.stream_preset_id is not None:
        return await _get_preset(session, subscription.stream_preset_id)
    return await _get_preset(session, subscription.preset_id)


def effective_cookie_id(subscription: Subscription, preset: Preset | None) -> int | None:
    """The subscription's own cookies file wins over the preset's."""
    if subscription.cookie_id is not None:
        return subscription.cookie_id
    return preset.cookie_id if preset else None


async def _output_dir(context: WatchContext, session: AsyncSession, requested: str | None) -> str:
    base_dir = await auth_service.get_download_dir(session)
    if base_dir is None:
        raise EnqueueError("Finish setup first")
    try:
        extra_roots = context.settings.extra_download_roots
        return str(resolve_job_dir(requested, base_dir, extra_roots))
    except InvalidPathError as error:
        raise EnqueueError(str(error)) from error


# yt-dlp live_status values of streams that are recorded instead of downloaded.
STREAM_STATUSES = {"is_upcoming", "is_live"}


def _kind_and_status(video: Video) -> tuple[JobKind, JobStatus]:
    if video.live_status not in STREAM_STATUSES:
        return JobKind.DOWNLOAD, JobStatus.QUEUED
    return JobKind.LIVE, recording_status(video.release_at, utcnow())


async def _recording_plan(
    session: AsyncSession, video: Video, preset: Preset | None
) -> RecordingPlan:
    live_since = video.release_at if video.live_status == "is_live" else None
    settings = preset_recording(preset) or await default_recording(session)
    return plan_recording(settings, live_since, utcnow())


async def enqueue_video(
    context: WatchContext, session: AsyncSession, subscription: Subscription, video: Video
) -> Job:
    """Queues the download, or the recording for a stream. Options are copied from the
    preset, like the download form does."""
    kind, status = _kind_and_status(video)
    preset = await preset_for(session, subscription, stream=kind == JobKind.LIVE)
    requested_dir = subscription.output_dir or (preset.output_dir if preset else None)
    plan = await _recording_plan(session, video, preset) if kind == JobKind.LIVE else None
    job = Job(
        url=video_url(video.video_id),
        # Known from the feed or probe; shown until yt-dlp reports its own.
        title=video.title,
        status=status,
        kind=kind,
        scheduled_at=video.release_at if kind == JobKind.LIVE else None,
        **(dataclasses.asdict(plan) if plan else {}),
        options=dict(preset.options) if preset else {},
        extra_args=preset.extra_args if preset else "",
        cookie_id=effective_cookie_id(subscription, preset),
        output_dir=await _output_dir(context, session, requested_dir),
        folders=preset.folders if preset else None,
        file_name=preset.file_name if preset else None,
        media_files=preset.media_files if preset else False,
        proxy_mode=preset.proxy_mode if preset else "off",
        subscription_id=subscription.id,
    )
    session.add(job)
    await session.commit()
    # SQLite can reuse the id of a deleted job; a new job must not inherit its log.
    job_log_path(context.settings, job.id).unlink(missing_ok=True)
    publish_job(context.hub, job)
    if status == JobStatus.QUEUED:
        # Scheduled recordings are queued later by the live scheduler.
        context.jobs.submit(job)
    return job
