"""Folder and file-name layout, and the extra files media servers read.

Three independent choices per preset or download:

- folders: straight into the download folder, a folder per channel, or a folder per
  channel with a "Season YYYY" folder per year;
- file name: the user's own template (or yt-dlp's default), "Title [id]",
  "[20261103] Title", "[20261103] Title [id]", or a TV episode numbered by the day it aired
  ("Channel - S2026E1103 - Title [id]"), so new videos sort in order without a running
  count;
- media files: a .jpg thumbnail and .nfo next to each video, and the channel's tvshow.nfo
  and artwork, for Jellyfin, Plex and Kodi.

On top of the folders, a video folder can hold each video with the files saved beside it
(.nfo, thumbnail, subtitles, live chat), named like the video: "Channel/[20261103] Title/
[20261103] Title.mkv". The channel's tvshow.nfo and artwork stay in the channel folder.
"""

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.common import FileNaming, FolderLayout
from yt_dlp_z.services.ytdlp.command import NFO_MARKER

CHANNEL = "%(channel,uploader|Unknown channel)s"
# The day it aired: a live stream's or premiere's release date, else the upload date.
# upload_date alone is when a stream's waiting room was made, often weeks before.
# yt-dlp ignores a date format on a field with alternatives, so it gets its own field.
AIR_DATE_ARGS = ["--parse-metadata", r"%(release_date,upload_date|)s:(?P<air_date>\d{8})"]
YEAR = "%(air_date>%Y|0000)s"
DATE = "%(air_date|00000000)s"

FOLDERS: dict[FolderLayout, str] = {
    "channel": CHANNEL,
    "season": f"{CHANNEL}/Season {YEAR}",
}
# Titles are cut so the whole name fits the 255-byte limit.
FILE_NAMES: dict[FileNaming, str] = {
    "title_id": "%(title).200B [%(id)s].%(ext)s",
    "dated": f"[{DATE}] %(title).200B.%(ext)s",
    "dated_id": f"[{DATE}] %(title).190B [%(id)s].%(ext)s",
    "episode": f"{CHANNEL} - S{YEAR}E%(air_date>%m%d|0000)s - %(title).150B [%(id)s].%(ext)s",
}
EXT = ".%(ext)s"
# What yt-dlp names files when no template is given.
YTDLP_DEFAULT_NAME = "%(title)s [%(id)s].%(ext)s"

NFO_FIELDS = (
    "filepath,id,title,channel,uploader,channel_id,air_date,upload_date,description,duration"
)


def _user_template(job: Job) -> str | None:
    template = job.options.get("--output")
    return template if isinstance(template, str) and template else None


def has_layout(job: Job) -> bool:
    return job.folders is not None or job.file_name is not None or job.video_folder


def in_own_folder(name: str) -> str:
    """ "[x] Title.%(ext)s" → "[x] Title/[x] Title.%(ext)s"; any folders before it are kept."""
    head, slash, file_template = name.rpartition("/")
    folder = file_template.removesuffix(EXT)
    return f"{head}{slash}{folder}/{file_template}"


def output_template(job: Job) -> str | None:
    """The file name template the job's files get: the layout's, or the user's own."""
    user = _user_template(job)
    if not has_layout(job):
        return user
    name = FILE_NAMES[job.file_name] if job.file_name else (user or YTDLP_DEFAULT_NAME)
    if job.video_folder:
        name = in_own_folder(name)
    return f"{FOLDERS[job.folders]}/{name}" if job.folders else name


def job_media_args(job: Job) -> list[str]:
    """Options yt-dlp-z adds for the layout. They come after the user's own, so this
    file name template wins over theirs."""
    args: list[str] = []
    if has_layout(job) or job.media_files:
        args += AIR_DATE_ARGS
    if has_layout(job):
        args += ["--output", output_template(job) or YTDLP_DEFAULT_NAME]
    if job.media_files:
        args += [
            # Saved next to the video with the same name, where media servers look for it.
            "--write-thumbnail",
            "--convert-thumbnails",
            "jpg",
            "--embed-metadata",
            # What the episode .nfo needs, printed once the file is in place.
            "--print",
            f"after_move:{NFO_MARKER}%(.{{{NFO_FIELDS}}})j",
        ]
    return args
