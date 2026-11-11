from pydantic import BaseModel, Field, field_validator

from yt_dlp_z.schemas.common import WebUrl
from yt_dlp_z.services.align.job import AlignState


class AlignRequest(BaseModel):
    """Recordings of the same event (collab streams) to line up against the first one."""

    urls: list[WebUrl] = Field(min_length=2, max_length=4)
    # For members-only streams, or when the server needs to be signed in.
    cookie_id: int | None = None

    @field_validator("urls")
    @classmethod
    def _distinct(cls, urls: list[str]) -> list[str]:
        if len(set(urls)) != len(urls):
            raise ValueError("Each link can only be listed once")
        return urls


class AlignCreated(BaseModel):
    id: str


class AlignStatus(BaseModel):
    id: str
    state: AlignState
    # 0 to 1 over the whole job.
    progress: float
    # Per link, seconds by which its content is later than the first link's (the first is
    # 0). Add it to a moment in the first recording to find it in this one. null when no
    # reliable match was found (they don't overlap, or the audio is too different).
    offsets: dict[str, float | None]
    # Per link, the share of checked audio windows that agree with the offset (0 to 1).
    confidence: dict[str, float]
    error: str | None
