from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.routes.jobs import find_job
from yt_dlp_z.db.models.job import FINISHED_STATUSES, JobStatus, utcnow
from yt_dlp_z.schemas.jobs import JobOut
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.job_run import job_log_path, publish_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_auth)])

LOG_TAIL_BYTES = 200_000


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: int, state: State, db: Db) -> JobOut:
    job = await find_job(db, job_id)
    if job.status in FINISHED_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "This download has already finished")
    if job.status == JobStatus.QUEUED:
        await repository.save(db, job, status=JobStatus.CANCELLED, finished_at=utcnow())
        publish_job(state.hub, job)
    else:
        await state.jobs.cancel(job_id)
        await db.refresh(job)
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
    state.jobs.submit(job_id)
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
