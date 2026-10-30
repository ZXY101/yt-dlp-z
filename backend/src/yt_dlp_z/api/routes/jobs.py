from fastapi import APIRouter, Depends, HTTPException, Query, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.validation import check_user_args, output_dir_for_job
from yt_dlp_z.db.models.job import FINISHED_STATUSES, Job, JobStatus
from yt_dlp_z.schemas.jobs import JobCreate, JobDeletedEvent, JobOut
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.job_run import job_log_path, publish_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_auth)])


async def find_job(db: Db, job_id: int) -> Job:
    job = await repository.get_job(db, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Download not found")
    return job


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_job(body: JobCreate, state: State, db: Db) -> JobOut:
    await check_user_args(state, body.options, body.extra_args)
    output_dir = await output_dir_for_job(state, db, body.output_dir)
    job = Job(
        url=body.url,
        status=JobStatus.QUEUED,
        options=body.options,
        extra_args=body.extra_args,
        output_dir=str(output_dir),
    )
    db.add(job)
    await db.commit()
    # SQLite can reuse the id of a deleted job; a new job must not inherit its log.
    job_log_path(state.settings, job.id).unlink(missing_ok=True)
    publish_job(state.hub, job)
    state.jobs.submit(job.id)
    return JobOut.model_validate(job)


@router.get("")
async def list_jobs(db: Db, limit: int = Query(default=200, ge=1, le=1000)) -> list[JobOut]:
    return [JobOut.model_validate(job) for job in await repository.list_jobs(db, limit)]


@router.get("/{job_id}")
async def get_job(job_id: int, db: Db) -> JobOut:
    return JobOut.model_validate(await find_job(db, job_id))


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, state: State, db: Db) -> None:
    """Removes the job from history. Downloaded files are kept."""
    job = await find_job(db, job_id)
    if job.status not in FINISHED_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cancel the download before removing it")
    await db.delete(job)
    await db.commit()
    job_log_path(state.settings, job_id).unlink(missing_ok=True)
    state.hub.publish(JobDeletedEvent(id=job_id).model_dump(mode="json"))
