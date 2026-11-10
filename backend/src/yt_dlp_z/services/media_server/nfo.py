"""Writes Kodi-style .nfo files (read by Jellyfin, Emby and Kodi) for media-server output."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from yt_dlp_z.schemas.common import FolderLayout

SECONDS_PER_MINUTE = 60
DATE_LENGTH = 8


SHOW_NFO = "tvshow.nfo"


def _text(info: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = info.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _add(parent: ET.Element, tag: str, text: str | None) -> None:
    if text is not None:
        ET.SubElement(parent, tag).text = text


def _write(path: Path, root: ET.Element) -> None:
    ET.indent(root)
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _air_date(info: dict[str, Any]) -> str | None:
    date = _text(info, "air_date", "upload_date")
    if date is None or len(date) != DATE_LENGTH or not date.isdigit():
        return None
    return date


def episode_nfo(info: dict[str, Any]) -> ET.Element:
    root = ET.Element("episodedetails")
    _add(root, "title", _text(info, "title"))
    _add(root, "showtitle", _text(info, "channel", "uploader"))
    date = _air_date(info)
    if date is not None:
        # Same numbers as the file name: season = year, episode = month and day.
        _add(root, "season", str(int(date[:4])))
        _add(root, "episode", str(int(date[4:])))
        _add(root, "aired", f"{date[:4]}-{date[4:6]}-{date[6:]}")
    _add(root, "plot", _text(info, "description"))
    duration = info.get("duration")
    if isinstance(duration, int | float) and duration > 0:
        _add(root, "runtime", str(max(1, round(duration / SECONDS_PER_MINUTE))))
    _add(root, "studio", _text(info, "channel", "uploader"))
    video_id = _text(info, "id")
    if video_id is not None:
        ET.SubElement(root, "uniqueid", type="youtube", default="true").text = video_id
    return root


def show_nfo(info: dict[str, Any]) -> ET.Element:
    root = ET.Element("tvshow")
    _add(root, "title", _text(info, "channel", "uploader"))
    channel_id = _text(info, "channel_id")
    if channel_id is not None:
        ET.SubElement(root, "uniqueid", type="youtube", default="true").text = channel_id
    return root


def show_folder(video: Path, folders: FolderLayout | None, video_folder: bool) -> Path:
    """The channel folder above a video: past its own folder and its season folder."""
    levels = (1 if folders == "season" else 0) + (1 if video_folder else 0)
    return video.parents[levels]


def write_nfo_files(
    info: dict[str, Any], layout: tuple[FolderLayout | None, bool], download_dir: Path
) -> Path | None:
    """The episode's .nfo next to its file, and the channel's tvshow.nfo once.
    Files outside the download folder are left alone. Returns the channel folder, if it
    is inside the download folder."""
    filepath = _text(info, "filepath")
    if filepath is None:
        return None
    video = Path(filepath).resolve()
    if not video.is_relative_to(download_dir.resolve()):
        return None
    _write(video.with_suffix(".nfo"), episode_nfo(info))
    folders, video_folder = layout
    show_dir = show_folder(video, folders, video_folder)
    show_file = show_dir / SHOW_NFO
    inside = show_dir != download_dir.resolve() and show_dir.is_relative_to(download_dir.resolve())
    if not inside:
        return None
    if not show_file.exists():
        _write(show_file, show_nfo(info))
    return show_dir
