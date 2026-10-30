from collections.abc import Sequence
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job, JobStatus, utcnow

INTERRUPTED_MESSAGE = "Interrupted because yt-dlp-z stopped. Retry to start again."


async def get_job(session: AsyncSession, job_id: int) -> Job | None:
    return await session.get(Job, job_id)


async def list_jobs(session: AsyncSession, limit: int) -> Sequence[Job]:
    result = await session.execute(select(Job).order_by(Job.id.desc()).limit(limit))
    return result.scalars().all()


async def save(session: AsyncSession, job: Job, **changes: Any) -> Job:
    for name, value in changes.items():
        setattr(job, name, value)
    job.revision += 1
    await session.commit()
    return job


async def recover_after_restart(session: AsyncSession) -> list[int]:
    """Fails jobs that were mid-download when the app stopped; returns queued job ids."""
    await session.execute(
        update(Job)
        .where(Job.status == JobStatus.RUNNING)
        .values(
            status=JobStatus.FAILED,
            error=INTERRUPTED_MESSAGE,
            finished_at=utcnow(),
            revision=Job.revision + 1,
        )
    )
    await session.commit()
    result = await session.execute(
        select(Job.id).where(Job.status == JobStatus.QUEUED).order_by(Job.id)
    )
    return list(result.scalars().all())


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
