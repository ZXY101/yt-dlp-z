"""The files a job left on disk, for disk usage and for deleting them.

yt-dlp reports the media files it saved (job.files). Files saved beside each one with the
same name are the job's too: its .nfo, thumbnail, subtitles, and other recording parts
("Title [id] (part 2).mp4"). Only files inside the job's own download folder are ever
returned, so a moved or renamed folder can't make this touch anything else.

Deleting a channel's last video also removes its tvshow.nfo and artwork, so media servers
don't keep showing an empty show.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.services.media_server.artwork import ARTWORK
from yt_dlp_z.services.media_server.nfo import SHOW_NFO

PART_SUFFIX = re.compile(r" \(part \d+\)$")
CHANNEL_FILES = {SHOW_NFO, *ARTWORK}


@dataclass(frozen=True)
class DiskUsage:
    files: int
    bytes: int


def _belongs(name: str, base: str) -> bool:
    # The same name, maybe a part number, then only extensions (".ja.srt", ".nfo",
    # ".f303.mp4.part"): "Clip.mp4" must not claim "Clip.b [x].mp4".
    return re.fullmatch(rf"{re.escape(base)}( \(part \d+\))?(\.[\w-]+)+", name) is not None


def _beside(media: Path) -> list[Path]:
    """The media file and the files saved beside it with the same name."""
    base = PART_SUFFIX.sub("", media.stem)
    try:
        entries = list(media.parent.iterdir())
    except OSError:
        return []
    return [entry for entry in entries if entry.is_file() and _belongs(entry.name, base)]


def _inside(path: Path, folder: Path) -> bool:
    try:
        return path.resolve().is_relative_to(folder)
    except OSError:
        return False


def job_files(job: Job) -> list[Path]:
    folder = Path(job.output_dir).resolve()
    media = job.files or ([job.filepath] if job.filepath else [])
    found: dict[Path, None] = {}
    for file in media:
        for path in _beside(Path(file)):
            if _inside(path, folder):
                found[path] = None
    return sorted(found)


def disk_usage(jobs: list[Job]) -> DiskUsage:
    paths = {path for job in jobs for path in job_files(job)}
    total = 0
    for path in paths:
        try:
            total += path.stat().st_size
        except OSError:
            continue
    return DiskUsage(files=len(paths), bytes=total)


def delete_job_files(job: Job) -> int:
    """Deletes the job's files and any folders that became empty below its download
    folder (an empty "Season 2026", a channel folder with only its tvshow.nfo and artwork
    left). Returns how many of the job's files were deleted."""
    folder = Path(job.output_dir).resolve()
    deleted = 0
    parents: set[Path] = set()
    for path in job_files(job):
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        deleted += 1
        parents.add(path.parent.resolve())
    for parent in sorted(parents, key=lambda item: len(item.parts), reverse=True):
        _remove_empty_folders(parent, folder)
    return deleted


def _remove_leftover_channel_files(folder: Path) -> None:
    """Only in a channel folder (it has a tvshow.nfo) that holds nothing else."""
    try:
        names = {entry.name for entry in folder.iterdir()}
        if SHOW_NFO in names and names <= CHANNEL_FILES:
            for name in names:
                (folder / name).unlink(missing_ok=True)
    except OSError:
        return


def _remove_empty_folders(start: Path, stop: Path) -> None:
    current = start
    while current != stop and current.is_relative_to(stop):
        _remove_leftover_channel_files(current)
        try:
            current.rmdir()  # only succeeds when empty
        except OSError:
            return
        current = current.parent
