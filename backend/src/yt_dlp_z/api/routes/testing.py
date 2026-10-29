"""Endpoints for the E2E suite. Only mounted when YTDLPZ_TEST_MODE is set."""

from fastapi import APIRouter, status
from sqlalchemy import delete

from yt_dlp_z.api.deps import Db, State
from yt_dlp_z.db.base import Base

router = APIRouter(prefix="/api/test", tags=["testing"], include_in_schema=False)


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset(state: State, db: Db) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(delete(table))
    await db.commit()
    state.login_limiter.reset()
