"""Removing a finished job from history, and optionally its files from disk."""

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import Job
from yt_dlp_z.db.models.video import Video, VideoState
from yt_dlp_z.schemas.jobs import JobDeletedEvent
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.jobs.context import job_log_path
from yt_dlp_z.services.jobs.files import delete_job_files
from yt_dlp_z.services.live_chat.split import discard_capture

logger = logging.getLogger(__name__)

DELETED_REASON = "Its files were deleted"


async def _never_download_again(session: AsyncSession, job: Job, reason: str) -> None:
    """A subscription would otherwise never look at the video again anyway, but a failed
    or retried one could; marking it ignored also shows in the channel's video list."""
    videos = await session.execute(select(Video).where(Video.job_id == job.id))
    for video in videos.scalars():
        video.state = VideoState.IGNORED
        video.reason = reason


@dataclass(frozen=True)
class JobRemover:
    settings: Settings
    hub: EventHub

    async def remove(
        self, session: AsyncSession, job: Job, *, delete_files: bool, reason: str = DELETED_REASON
    ) -> int:
        """Returns how many files were deleted."""
        deleted = 0
        if delete_files:
            deleted = await asyncio.to_thread(delete_job_files, job)
            await _never_download_again(session, job, reason)
            logger.info("Deleted %s files of job %s", deleted, job.id)
        job_id = job.id
        await session.delete(job)
        await session.commit()
        job_log_path(self.settings, job_id).unlink(missing_ok=True)
        discard_capture(self.settings, job_id)
        self.hub.publish(JobDeletedEvent(id=job_id).model_dump(mode="json"))
        return deleted
