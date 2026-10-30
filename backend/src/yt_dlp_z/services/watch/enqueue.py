"""Creates the download job for a subscription's new video, using its preset."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import Job, JobStatus
from yt_dlp_z.db.models.preset import Preset
from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.services import auth_service
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.jobs.job_run import job_log_path, publish_job
from yt_dlp_z.services.jobs.manager import JobManager
from yt_dlp_z.services.paths import InvalidPathError, resolve_job_dir
from yt_dlp_z.services.watch.probe import video_url


@dataclass(frozen=True)
class WatchContext:
    session_factory: async_sessionmaker[AsyncSession]
    settings: Settings
    hub: EventHub
    jobs: JobManager


class EnqueueError(Exception):
    pass


async def preset_for(session: AsyncSession, subscription: Subscription) -> Preset | None:
    if subscription.preset_id is None:
        return None
    return await session.get(Preset, subscription.preset_id)


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


async def enqueue_video(
    context: WatchContext, session: AsyncSession, subscription: Subscription, video_id: str
) -> Job:
    """Queues the download. Options are copied from the preset, like the download form does."""
    preset = await preset_for(session, subscription)
    requested_dir = subscription.output_dir or (preset.output_dir if preset else None)
    job = Job(
        url=video_url(video_id),
        status=JobStatus.QUEUED,
        options=dict(preset.options) if preset else {},
        extra_args=preset.extra_args if preset else "",
        cookie_id=effective_cookie_id(subscription, preset),
        output_dir=await _output_dir(context, session, requested_dir),
        subscription_id=subscription.id,
    )
    session.add(job)
    await session.commit()
    # SQLite can reuse the id of a deleted job; a new job must not inherit its log.
    job_log_path(context.settings, job.id).unlink(missing_ok=True)
    publish_job(context.hub, job)
    context.jobs.submit(job.id)
    return job
