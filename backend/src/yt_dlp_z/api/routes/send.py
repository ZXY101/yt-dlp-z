from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.routes.jobs import create_job
from yt_dlp_z.api.routes.media import probe
from yt_dlp_z.api.validation import output_dir_for_job
from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.jobs import JobCreate, JobOut
from yt_dlp_z.schemas.media import MediaProbeRequest
from yt_dlp_z.schemas.presets import PresetOut
from yt_dlp_z.schemas.send import LinkJob, LinkJobs, LinkJobsRequest, SendRequest, SentLink
from yt_dlp_z.services import presets
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.duplicates import find_same_job
from yt_dlp_z.services.jobs.link_key import job_link_key, link_key
from yt_dlp_z.services.jobs.preset_plan import (
    default_preset,
    is_video_in_playlist,
    job_from_preset,
    recording_request,
    with_playlist_choice,
)

# Enough history for "you already downloaded this" without reading the whole table.
RECENT_JOBS = 500
MAX_LINK_JOBS = 5

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_auth)])


async def _preset_dicts(db: Db) -> list[dict[str, Any]]:
    rows = await presets.list_presets(db)
    return [PresetOut.model_validate(row).model_dump(mode="json") for row in rows]


def _chosen_preset(preset_list: list[dict[str, Any]], preset_id: int | None) -> Any:
    if preset_id is None:
        return None
    chosen = next((preset for preset in preset_list if preset["id"] == preset_id), None)
    if chosen is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "That preset doesn't exist")
    return chosen


def _refuse_whole_list(info: dict[str, Any]) -> None:
    count = info["entry_count"] or "an unknown number of"
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        f"This is a {info['kind']} with {count} videos. Set whole_playlist to download them all.",
    )


@router.post("/send", status_code=status.HTTP_201_CREATED)
async def send_link(body: SendRequest, state: State, db: Db) -> SentLink:
    """Downloads a link with a preset, or records it if it's a live or upcoming stream.

    Applies the preset on the server as the download form does, so a client only sends the
    link. The only way a send-only token can start a download. If the same link with the same
    settings is already queued, running or downloaded, returns that job (existing: true)."""
    preset_list = await _preset_dicts(db)
    chosen = _chosen_preset(preset_list, body.preset_id)
    alone = is_video_in_playlist(body.url) and not body.whole_playlist
    probe_request = MediaProbeRequest(
        url=body.url, cookie_id=chosen["cookie_id"] if chosen else None, no_playlist=alone
    )
    info = (await probe(probe_request, state, db)).model_dump(mode="json")
    if info["kind"] in {"playlist", "channel"} and not body.whole_playlist:
        _refuse_whole_list(info)
    preset_used = chosen or default_preset(preset_list, info["kind"])
    job = with_playlist_choice(job_from_preset(preset_used), body.url, body.whole_playlist)
    job.update(url=body.url, title=info["title"])
    if info["kind"] in {"live", "upcoming"}:
        job["recording"] = recording_request(preset_used, preset_list, info)
    preset_name = preset_used["name"] if preset_used else None
    new_job = JobCreate.model_validate(job)
    existing = await _same_job(state, db, new_job.model_dump())
    if existing is not None:
        return SentLink(job=JobOut.model_validate(existing), preset=preset_name, existing=True)
    created = await create_job(new_job, state, db)
    return SentLink(job=created, preset=preset_name)


async def _same_job(state: State, db: Db, planned: dict[str, Any]) -> Job | None:
    output_dir = await output_dir_for_job(state, db, planned.get("output_dir"))
    rows = await repository.list_jobs(db, RECENT_JOBS, None)
    return find_same_job(rows, planned, str(output_dir))


@router.post("/for-link")
async def jobs_for_link(body: LinkJobsRequest, db: Db) -> LinkJobs:
    """The newest jobs for a link, with their progress, so a client can show a download that is
    already running instead of starting another.

    Matches the same video, playlist or page however the link is written (tracking
    parameters, youtu.be, shorts). Looks at the most recent 500 jobs."""
    wanted = link_key(body.url, whole_playlist=body.whole_playlist)
    rows = await repository.list_jobs(db, RECENT_JOBS, None)
    matches = [row for row in rows if job_link_key(row.url, row.options or {}) == wanted]
    return LinkJobs(jobs=[LinkJob.model_validate(row) for row in matches[:MAX_LINK_JOBS]])
