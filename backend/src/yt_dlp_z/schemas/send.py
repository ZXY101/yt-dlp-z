from pydantic import BaseModel

from yt_dlp_z.schemas.common import WebUrl
from yt_dlp_z.schemas.jobs import JobOut


class SendRequest(BaseModel):
    """A link to download with a preset; the server works out the rest."""

    url: WebUrl
    # Empty: the default preset for this kind of link.
    preset_id: int | None = None
    # Required to download a whole playlist or channel. For a video opened from a playlist
    # (watch?v=…&list=…), picks the playlist instead of the video alone.
    whole_playlist: bool = False


class SentLink(BaseModel):
    job: JobOut
    # The preset used, if any.
    preset: str | None
