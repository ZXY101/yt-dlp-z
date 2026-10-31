"""Media-server output: files laid out the way Jellyfin, Plex and Kodi expect a TV show.

Each channel is a show, each upload year a season and each video an episode numbered by
its upload date (S2026E1031), so new videos sort in order without a running count.
"""

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.common import MediaLayout
from yt_dlp_z.services.ytdlp.command import NFO_MARKER

CHANNEL = "%(channel,uploader|Unknown channel)s"
YEAR = "%(upload_date>%Y|0000)s"
# Titles are cut to 150 bytes: channel, title and the rest must fit the 255-byte name limit.
EPISODE = f"{CHANNEL} - S{YEAR}E%(upload_date>%m%d|0000)s - %(title).150B [%(id)s].%(ext)s"

NFO_FIELDS = "filepath,id,title,channel,uploader,channel_id,upload_date,description,duration"


def media_template(layout: MediaLayout) -> str:
    if layout == "season":
        return f"{CHANNEL}/Season {YEAR}/{EPISODE}"
    return f"{CHANNEL}/{EPISODE}"


def media_args(layout: MediaLayout) -> list[str]:
    """Options yt-dlp-z adds for a media-server layout. They come after the user's own,
    so this file name template wins over theirs."""
    return [
        "--output",
        media_template(layout),
        # Saved next to the video with the same name, where media servers look for it.
        "--write-thumbnail",
        "--convert-thumbnails",
        "jpg",
        "--embed-metadata",
        # What the episode .nfo needs, printed once the file is in place.
        "--print",
        f"after_move:{NFO_MARKER}%(.{{{NFO_FIELDS}}})j",
    ]


def output_template(job: Job) -> str | None:
    """The file name template the job's files get: the media-server one, or the user's."""
    if job.media_layout is not None:
        return media_template(job.media_layout)
    template = job.options.get("--output")
    return template if isinstance(template, str) else None


def job_media_args(job: Job) -> list[str]:
    return media_args(job.media_layout) if job.media_layout is not None else []
