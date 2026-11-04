from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.validation import check_cookie_id, check_user_args, output_dir_for_job
from yt_dlp_z.db.models.job import FINISHED_STATUSES, Job, JobKind, JobStatus, utcnow
from yt_dlp_z.schemas.jobs import JobCreate, JobOut, RecordingRequest
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import job_log_path, publish_job
from yt_dlp_z.services.jobs.removal import JobRemover
from yt_dlp_z.services.live.plan import hours_to_seconds
from yt_dlp_z.services.live.scheduler import recording_status

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_auth)])


async def find_job(db: Db, job_id: int) -> Job:
    job = await repository.get_job(db, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Download not found")
    return job


def _recording_fields(recording: RecordingRequest) -> dict[str, Any]:
    return {
        "kind": JobKind.LIVE,
        "status": recording_status(recording.starts_at, utcnow()),
        "scheduled_at": recording.starts_at,
        "record_from_start": recording.from_start,
        "part_seconds": hours_to_seconds(recording.part_hours),
        "max_seconds": hours_to_seconds(recording.max_hours),
        "vod_after_seconds": hours_to_seconds(recording.vod_after_hours),
        "vod_replace": recording.vod_replace,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_job(body: JobCreate, state: State, db: Db) -> JobOut:
    await check_user_args(state, body.options, body.extra_args)
    await check_cookie_id(db, body.cookie_id)
    output_dir = await output_dir_for_job(state, db, body.output_dir)
    kind_fields: dict[str, Any] = {"status": JobStatus.QUEUED}
    if body.recording is not None:
        kind_fields = _recording_fields(body.recording)
    job = Job(
        url=body.url,
        title=body.title,
        **kind_fields,
        options=body.options,
        extra_args=body.extra_args,
        output_dir=str(output_dir),
        folders=body.folders,
        file_name=body.file_name,
        media_files=body.media_files,
        live_chat=body.live_chat.model_dump() if body.live_chat else None,
        proxy_mode=body.proxy_mode,
        cookie_id=body.cookie_id,
    )
    db.add(job)
    await db.commit()
    # SQLite can reuse the id of a deleted job; a new job must not inherit its log.
    job_log_path(state.settings, job.id).unlink(missing_ok=True)
    publish_job(state.hub, job)
    if job.status == JobStatus.QUEUED:
        # Scheduled recordings are queued later by the live scheduler.
        state.jobs.submit(job)
    return JobOut.model_validate(job)


@router.get("")
async def list_jobs(
    db: Db,
    limit: int = Query(default=200, ge=1, le=1000),
    subscription_id: int | None = None,
) -> list[JobOut]:
    """Newest first. subscription_id: only what that channel subscription queued."""
    jobs = await repository.list_jobs(db, limit, subscription_id)
    return [JobOut.model_validate(job) for job in jobs]


@router.get("/{job_id}")
async def get_job(job_id: int, db: Db) -> JobOut:
    return JobOut.model_validate(await find_job(db, job_id))


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, state: State, db: Db, delete_files: bool = False) -> None:
    """Removes the job from history. With delete_files, also deletes what it saved (and
    files beside them: .nfo, thumbnail, subtitles), and a subscription won't download
    the video again."""
    job = await find_job(db, job_id)
    if job.status not in FINISHED_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cancel the download before removing it")
    await JobRemover(state.settings, state.hub).remove(db, job, delete_files=delete_files)
