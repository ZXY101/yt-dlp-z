from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.api.validation import check_cookie_id
from yt_dlp_z.schemas.align import AlignCreated, AlignRequest, AlignStatus, AlignStreamStatus
from yt_dlp_z.services.align.job import AlignBusyError, AlignJob

router = APIRouter(prefix="/api/align", tags=["align"], dependencies=[Depends(require_auth)])

NOT_FOUND = "No such alignment (finished ones are dropped after an hour without a check)"


def _status(job: AlignJob) -> AlignStatus:
    return AlignStatus(
        id=job.id,
        state=job.state,
        progress=round(job.progress, 3),
        streams=[
            AlignStreamStatus(
                url=stream.url, stage=stream.stage, downloaded=round(stream.downloaded, 3)
            )
            for stream in job.streams
        ],
        offsets=dict(job.offsets),
        confidence=dict(job.confidence),
        error=job.error,
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def start_alignment(body: AlignRequest, state: State, db: Db) -> AlignCreated:
    """Finds how far apart 2 to 4 recordings of the same event are, from their audio, in the
    background. The server downloads a small audio-only copy of each, compares them and
    deletes them again; nothing is kept. One alignment runs at a time."""
    await check_cookie_id(db, body.cookie_id)
    try:
        job = state.align.create(list(body.urls), body.cookie_id)
    except AlignBusyError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return AlignCreated(id=job.id)


@router.get("/{align_id}")
async def get_alignment(align_id: str, state: State) -> AlignStatus:
    """The alignment's progress and, once done, the offsets. Results are dropped after an
    hour without a check."""
    job = state.align.get(align_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return _status(job)


@router.delete("/{align_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alignment(align_id: str, state: State) -> None:
    """Stops the alignment if it's running and deletes its audio and result."""
    if not await state.align.delete(align_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
