"""Downloads a stream's VOD some time after its recording, when the live preset says so.

A recording can have gaps (expired links, restarts); the VOD YouTube keeps afterwards
usually has none and is often better quality. The VOD is a normal download, scheduled
like a recording, with " (VOD)" added to its title so it never has the recording's file
name (yt-dlp would take the recording for the finished download). With vod_replace, the
recording is deleted once the VOD is saved, unless the VOD looks edited (vod_check.py); a VOD
that fails keeps the recording.
"""

import logging
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job, JobKind, JobStatus, utcnow
from yt_dlp_z.db.models.video import Video
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import JobContext, job_log_path, publish_job
from yt_dlp_z.services.jobs.removal import JobRemover
from yt_dlp_z.services.live.vod_check import reason_to_keep

logger = logging.getLogger(__name__)

# Stopped recordings keep what they recorded; their VOD is still worth having.
SAVED = (JobStatus.COMPLETED, JobStatus.CANCELLED)
VOD_ARGS = ["--replace-in-metadata", "title", r"^(.*)$", r"\1 (VOD)"]


def vod_args(job: Job) -> list[str]:
    return VOD_ARGS if job.source_job_id is not None else []


async def _has_vod(session: AsyncSession, recording: Job) -> bool:
    found = await session.execute(select(Job.id).where(Job.source_job_id == recording.id))
    return found.first() is not None


async def _schedule_vod(context: JobContext, session: AsyncSession, recording: Job) -> None:
    delay = timedelta(seconds=recording.vod_after_seconds or 0)
    vod = Job(
        url=recording.url,
        title=recording.title,
        status=JobStatus.SCHEDULED,
        kind=JobKind.DOWNLOAD,
        scheduled_at=utcnow() + delay,
        options=dict(recording.options),
        extra_args=recording.extra_args,
        cookie_id=recording.cookie_id,
        subscription_id=recording.subscription_id,
        output_dir=recording.output_dir,
        folders=recording.folders,
        file_name=recording.file_name,
        media_files=recording.media_files,
        video_folder=recording.video_folder,
        live_chat=recording.live_chat,
        proxy_mode=recording.proxy_mode,
        source_job_id=recording.id,
        vod_replace=recording.vod_replace,
    )
    session.add(vod)
    await session.commit()
    job_log_path(context.settings, vod.id).unlink(missing_ok=True)
    publish_job(context.hub, vod)
    logger.info("Scheduled the VOD of job %s as job %s", recording.id, vod.id)


async def _replace_recording(context: JobContext, session: AsyncSession, vod: Job) -> None:
    recording = await session.get(Job, vod.source_job_id)
    if recording is None or recording.status not in SAVED:
        return
    reason = await reason_to_keep(recording, vod)
    if reason is not None:
        await repository.save(session, vod, vod_note=reason)
        publish_job(context.hub, vod)
        with job_log_path(context.settings, vod.id).open("a", encoding="utf-8") as log:
            log.write(f"[yt-dlp-z] {reason}\n")
        logger.info("Job %s: %s", recording.id, reason)
        return
    # The subscription's video now points at the VOD, so deleting the recording doesn't
    # mark the video as deleted.
    await session.execute(update(Video).where(Video.job_id == recording.id).values(job_id=vod.id))
    await JobRemover(context.settings, context.hub).remove(session, recording, delete_files=True)
    logger.info("Deleted recording %s; its VOD is job %s", recording.id, vod.id)


async def after_finish(context: JobContext, session: AsyncSession, job: Job) -> None:
    """Called when any job finishes."""
    recorded = job.kind == JobKind.LIVE and job.status in SAVED and bool(job.files)
    if recorded and job.vod_after_seconds and not await _has_vod(session, job):
        await _schedule_vod(context, session, job)
        return
    replace = job.source_job_id is not None and job.vod_replace
    if replace and job.status == JobStatus.COMPLETED and job.files:
        await _replace_recording(context, session, job)
