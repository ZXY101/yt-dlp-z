"""Starts scheduled recordings shortly before their stream begins.

Recordings wait in the DB (status "scheduled") rather than in a yt-dlp process, so a
premiere a week away holds no process or queue slot, and survives restarts. yt-dlp's
--wait-for-video covers streams that start late.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from yt_dlp_z.db.models.job import JobStatus, utcnow
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import JobContext, publish_job
from yt_dlp_z.services.jobs.queues import JobQueues

logger = logging.getLogger(__name__)

TICK_SECONDS = 30
# Started this long before the announced time, so yt-dlp is waiting when the stream opens.
LEAD_TIME = timedelta(minutes=5)


def as_utc(value: datetime) -> datetime:
    """SQLite drops the timezone; stored values are UTC."""
    return value if value.tzinfo else value.replace(tzinfo=utcnow().tzinfo)


def recording_status(scheduled_at: datetime | None, now: datetime) -> JobStatus:
    """A new recording waits only if its stream starts later than the lead time."""
    if scheduled_at is None or as_utc(scheduled_at) <= now + LEAD_TIME:
        return JobStatus.QUEUED
    return JobStatus.SCHEDULED


class LiveScheduler:
    def __init__(self, context: JobContext, queues: JobQueues) -> None:
        self._context = context
        self._queues = queues
        self._loop: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._loop = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._loop is None:
            return
        self._loop.cancel()
        await asyncio.gather(self._loop, return_exceptions=True)

    async def queue_due(self) -> None:
        async with self._context.session_factory() as session:
            for job in await repository.due_recordings(session, utcnow() + LEAD_TIME):
                await repository.save(session, job, status=JobStatus.QUEUED)
                publish_job(self._context.hub, job)
                self._queues.submit(job)

    async def _run(self) -> None:
        while True:
            try:
                await self.queue_due()
            except Exception:
                logger.exception("The live scheduler crashed; retrying next tick")
            await asyncio.sleep(TICK_SECONDS)
