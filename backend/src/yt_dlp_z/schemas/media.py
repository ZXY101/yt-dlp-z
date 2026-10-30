from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from yt_dlp_z.schemas.common import WebUrl

# "channel": a page whose entries are playlists (a YouTube channel's tabs).
MediaKind = Literal["video", "playlist", "channel", "live", "upcoming"]


class MediaProbeRequest(BaseModel):
    url: WebUrl
    # Cookies decide what yt-dlp can see (members-only videos), so the check uses them too.
    cookie_id: int | None = None
    # For a video opened from a playlist: look at the video alone.
    no_playlist: bool = False


class MediaInfo(BaseModel):
    """What a link points at, checked before it is downloaded."""

    kind: MediaKind
    title: str | None
    uploader: str | None
    thumbnail: str | None
    # The site's domain, e.g. "youtube.com"; else yt-dlp's name for it.
    site: str | None
    duration: int | None
    # Playlists: how many entries, when the site says or the list is short.
    entry_count: int | None
    # Upcoming streams: when they are due to start.
    starts_at: datetime | None
    # Live streams: when they went live, if known.
    live_since: datetime | None
    members_only: bool
    # Live streams: whether the recording settings would record from the start.
    record_from_start: bool | None
