from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.routes.jobs import create_job
from yt_dlp_z.api.routes.media import probe
from yt_dlp_z.schemas.jobs import JobCreate
from yt_dlp_z.schemas.media import MediaProbeRequest
from yt_dlp_z.schemas.presets import PresetOut
from yt_dlp_z.schemas.send import SendRequest, SentLink
from yt_dlp_z.services import presets
from yt_dlp_z.services.jobs.preset_plan import (
    default_preset,
    is_video_in_playlist,
    job_from_preset,
    recording_request,
    with_playlist_choice,
)

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
    link. The only way a send-only token can start a download."""
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
    created = await create_job(JobCreate.model_validate(job), state, db)
    return SentLink(job=created, preset=preset_used["name"] if preset_used else None)
