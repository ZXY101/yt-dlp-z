"""Deletes a subscription's downloads some days after they finish, when it is set to.

Off unless a subscription has keep_days. Pinned downloads (job.keep) are left alone, and
deleted videos are marked ignored so the subscription never downloads them again.
"""

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job, JobStatus, utcnow
from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.services.jobs.context import JobContext
from yt_dlp_z.services.jobs.removal import JobRemover

logger = logging.getLogger(__name__)

SWEEP_INTERVAL_SECONDS = 60 * 60
# Stopped recordings keep what they recorded, so they count as saved too.
SAVED = (JobStatus.COMPLETED, JobStatus.CANCELLED)


class RetentionSweeper:
    def __init__(self, context: JobContext) -> None:
        self._context = context
        self._remover = JobRemover(context.settings, context.hub)
        self._loop: asyncio.Task[None] | None = None

    async def sweep(self) -> int:
        """Returns how many downloads were deleted."""
        deleted = 0
        async with self._context.session_factory() as session:
            subscriptions = await session.execute(
                select(Subscription).where(Subscription.keep_days.is_not(None))
            )
            for subscription in subscriptions.scalars().all():
                deleted += await self._sweep_one(session, subscription)
        return deleted

    async def _sweep_one(self, session: AsyncSession, subscription: Subscription) -> int:
        days = subscription.keep_days or 0
        cutoff = utcnow() - timedelta(days=days)
        jobs = await session.execute(
            select(Job).where(
                Job.subscription_id == subscription.id,
                Job.status.in_(SAVED),
                Job.keep.is_(False),
                Job.finished_at < cutoff,
            )
        )
        reason = f"Deleted {days} days after it was downloaded"
        old = jobs.scalars().all()
        for job in old:
            await self._remover.remove(session, job, delete_files=True, reason=reason)
        if old:
            logger.info("Deleted %s old downloads of %s", len(old), subscription.name)
        return len(old)

    def start(self) -> None:
        self._loop = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._loop is None:
            return
        self._loop.cancel()
        await asyncio.gather(self._loop, return_exceptions=True)

    async def _run(self) -> None:
        while True:
            try:
                await self.sweep()
            except Exception:
                logger.exception("Deleting old downloads failed; trying again later")
            await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
