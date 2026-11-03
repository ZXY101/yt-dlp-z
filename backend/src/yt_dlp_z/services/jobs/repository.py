from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job, JobKind, JobStatus, utcnow

INTERRUPTED_MESSAGE = "Interrupted because yt-dlp-z stopped. Retry to start again."


async def get_job(session: AsyncSession, job_id: int) -> Job | None:
    return await session.get(Job, job_id)


async def list_jobs(
    session: AsyncSession, limit: int, subscription_id: int | None = None
) -> Sequence[Job]:
    query = select(Job).order_by(Job.id.desc()).limit(limit)
    if subscription_id is not None:
        query = query.where(Job.subscription_id == subscription_id)
    result = await session.execute(query)
    return result.scalars().all()


async def save(session: AsyncSession, job: Job, **changes: Any) -> Job:
    for name, value in changes.items():
        setattr(job, name, value)
    job.revision += 1
    await session.commit()
    return job


async def recover_after_restart(session: AsyncSession) -> list[tuple[int, JobKind]]:
    """Fails downloads that were running when the app stopped, and queues interrupted
    recordings again: a stream can't wait for someone to press Retry. They continue as the
    next part, from now (the part before was saved when the app stopped). Returns the
    queued jobs."""
    running = Job.status == JobStatus.RUNNING
    await session.execute(
        update(Job)
        .where(running, Job.kind == JobKind.DOWNLOAD)
        .values(
            status=JobStatus.FAILED,
            error=INTERRUPTED_MESSAGE,
            finished_at=utcnow(),
            revision=Job.revision + 1,
        )
    )
    await session.execute(
        update(Job)
        .where(running, Job.kind == JobKind.LIVE)
        .values(**retry_changes(), record_from_start=False, revision=Job.revision + 1)
    )
    await session.commit()
    result = await session.execute(
        select(Job.id, Job.kind).where(Job.status == JobStatus.QUEUED).order_by(Job.id)
    )
    return [(job_id, JobKind(kind)) for job_id, kind in result.all()]


async def due_recordings(session: AsyncSession, before: datetime) -> Sequence[Job]:
    """Scheduled recordings whose stream starts before the given time."""
    result = await session.execute(
        select(Job)
        .where(Job.status == JobStatus.SCHEDULED, Job.scheduled_at <= before)
        .order_by(Job.scheduled_at)
    )
    return result.scalars().all()


def retry_changes() -> dict[str, Any]:
    """Field values that put a finished job back in the queue."""
    return {
        "status": JobStatus.QUEUED,
        "progress": None,
        "downloaded_bytes": None,
        "total_bytes": None,
        "speed": None,
        "eta": None,
        "filepath": None,
        "error": None,
        "started_at": None,
        "finished_at": None,
    }
