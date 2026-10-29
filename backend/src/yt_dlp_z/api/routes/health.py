from importlib.metadata import version

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["health"])


class Health(BaseModel):
    status: str
    version: str


@router.get("/health")
async def get_health() -> Health:
    return Health(status="ok", version=version("yt-dlp-z"))
