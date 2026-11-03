from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.routes.jobs import find_job
from yt_dlp_z.api.state import AppState
from yt_dlp_z.db.models.job import FINISHED_STATUSES, Job, JobStatus, utcnow
from yt_dlp_z.schemas.jobs import JobOut
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import job_log_path, publish_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_auth)])

LOG_TAIL_BYTES = 200_000


async def stop_job(state: AppState, db: AsyncSession, job: Job) -> None:
    """Cancels a job that hasn't finished: a waiting one at once, a running one through
    its queue (a recording keeps what it recorded)."""
    if job.status in {JobStatus.SCHEDULED, JobStatus.QUEUED}:
        await repository.save(db, job, status=JobStatus.CANCELLED, finished_at=utcnow())
        publish_job(state.hub, job)
        return
    await state.jobs.cancel(job)
    await db.refresh(job)


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: int, state: State, db: Db) -> JobOut:
    job = await find_job(db, job_id)
    if job.status in FINISHED_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "This download has already finished")
    await stop_job(state, db, job)
    return JobOut.model_validate(job)


class KeepIn(BaseModel):
    keep: bool


@router.put("/{job_id}/keep")
async def set_keep(job_id: int, body: KeepIn, state: State, db: Db) -> JobOut:
    """Pins a download so its subscription's "delete after N days" leaves it alone."""
    job = await find_job(db, job_id)
    await repository.save(db, job, keep=body.keep)
    publish_job(state.hub, job)
    return JobOut.model_validate(job)


@router.post("/{job_id}/retry")
async def retry_job(job_id: int, state: State, db: Db) -> JobOut:
    job = await find_job(db, job_id)
    if job.status not in {JobStatus.FAILED, JobStatus.CANCELLED}:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only failed or cancelled downloads can retry"
        )
    await repository.save(db, job, **repository.retry_changes())
    publish_job(state.hub, job)
    state.jobs.submit(job)
    return JobOut.model_validate(job)


@router.get("/{job_id}/log", response_class=PlainTextResponse)
async def get_job_log(job_id: int, state: State, db: Db) -> str:
    await find_job(db, job_id)
    path = job_log_path(state.settings, job_id)
    if not path.exists():
        return ""
    with path.open("rb") as log:
        size = log.seek(0, 2)
        log.seek(max(0, size - LOG_TAIL_BYTES))
        return log.read().decode(errors="replace")
