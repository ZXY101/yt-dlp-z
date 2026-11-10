"""Finding a job that would make the same file as a new one, so sending a link twice doesn't
queue it twice. A different preset (other options, folder or name) is a new download; so is
a retry after a failure or cancel, or a finished download whose file is gone."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from yt_dlp_z.db.models.job import Job, JobKind, JobStatus
from yt_dlp_z.services.jobs.link_key import job_link_key

# What decides the file a job writes, besides the link.
SAME_FILE_FIELDS = (
    "options",
    "extra_args",
    "folders",
    "file_name",
    "media_files",
    "video_folder",
    "cookie_id",
)
RETRIED_STATUSES = {JobStatus.FAILED, JobStatus.CANCELLED}


def _planned_value(planned: dict[str, Any], field: str) -> Any:
    defaults: dict[str, Any] = {
        "options": {},
        "extra_args": "",
        "media_files": False,
        "video_folder": False,
    }
    return planned.get(field, defaults.get(field))


def _file_is_there(job: Job) -> bool:
    if job.status != JobStatus.COMPLETED or not job.filepath:
        return True
    return Path(job.filepath).exists()


def _same_settings(job: Job, planned: dict[str, Any], output_dir: str) -> bool:
    kind = JobKind.LIVE if planned.get("recording") else JobKind.DOWNLOAD
    if job.kind != kind or job.output_dir != output_dir:
        return False
    return all(getattr(job, field) == _planned_value(planned, field) for field in SAME_FILE_FIELDS)


def find_same_job(jobs: Iterable[Job], planned: dict[str, Any], output_dir: str) -> Job | None:
    """The newest queued, running or finished job for the same link with the same settings."""
    wanted = job_link_key(planned["url"], planned.get("options", {}))
    for job in jobs:
        if job.status in RETRIED_STATUSES:
            continue
        if job_link_key(job.url, job.options or {}) != wanted:
            continue
        if _same_settings(job, planned, output_dir) and _file_is_there(job):
            return job
    return None
