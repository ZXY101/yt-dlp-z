"""Parses the marker lines yt-dlp prints for yt-dlp-z (see command.py)."""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from yt_dlp_z.services.ytdlp.command import (
    CHAT_MARKER,
    FILE_MARKER,
    INFO_MARKER,
    NFO_MARKER,
    PROGRESS_MARKER,
)

PERCENT = 100
# When yt-dlp downloads several streams at once (live-from-start recordings fetch video and
# audio in parallel), it prefixes each progress line with the stream's number: "1: …".
PARALLEL_PREFIX = re.compile(r"^\d+: ")
# Recordings joined mid-stream are written by ffmpeg, which reports its own progress:
# "frame=  449 fps=112 q=-1.0 size=     512KiB time=00:00:14.96 bitrate= 280.2kbits/s".
FFMPEG_PROGRESS = re.compile(r"size=\s*(?P<size>[\d.]+)(?P<unit>[KMG]i?B|kB|B)\s+time=")
FFMPEG_TIME = re.compile(r"time=\s*(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>[\d.]+)")
FFMPEG_BITRATE = re.compile(r"bitrate=\s*(?P<kbits>[\d.]+)kbits/s")
UNIT_BYTES = {
    "B": 1,
    "kB": 1000,
    "KiB": 1024,
    "MiB": 1024**2,
    "MB": 1000**2,
    "GiB": 1024**3,
    "GB": 1000**3,
}


@dataclass(frozen=True)
class ProgressUpdate:
    downloaded_bytes: int | None
    total_bytes: int | None
    speed: float | None
    eta: int | None
    progress: float | None
    # Which of several parallel streams this is about (yt-dlp's progress_idx).
    part: int = 0
    # (fragments saved, newest fragment's number) when downloading a stream in fragments.
    fragments: tuple[int, int] | None = None
    # How far into its video ffmpeg is, when ffmpeg writes the file.
    media_seconds: float | None = None


@dataclass(frozen=True)
class InfoUpdate:
    title: str | None
    # When a live stream really started (epoch seconds).
    release_timestamp: float | None = None


@dataclass(frozen=True)
class FileUpdate:
    filepath: str


@dataclass(frozen=True)
class NfoUpdate:
    """A finished file's details, for its .nfo (media-server output)."""

    info: dict[str, Any]


@dataclass(frozen=True)
class ChatUpdate:
    """A finished video whose live chat the job should fetch afterwards."""

    filepath: str
    url: str
    live_status: str | None


Update = ProgressUpdate | InfoUpdate | FileUpdate | NfoUpdate | ChatUpdate


def _number(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    return float(value) if isinstance(value, int | float) else None


def _progress(data: dict[str, Any]) -> ProgressUpdate:
    downloaded = _number(data, "downloaded_bytes")
    total = _number(data, "total_bytes") or _number(data, "total_bytes_estimate")
    percent = None
    if data.get("status") == "finished":
        percent = float(PERCENT)
    elif downloaded is not None and total:
        percent = min(PERCENT, downloaded / total * PERCENT)
    eta = _number(data, "eta")
    part = data.get("progress_idx")
    index, count = data.get("fragment_index"), data.get("fragment_count")
    fragments = (index, count) if isinstance(index, int) and isinstance(count, int) else None
    return ProgressUpdate(
        downloaded_bytes=int(downloaded) if downloaded is not None else None,
        total_bytes=int(total) if total is not None else None,
        speed=_number(data, "speed"),
        eta=int(eta) if eta is not None else None,
        progress=percent,
        part=part if isinstance(part, int) else 0,
        fragments=fragments,
    )


def _total(values: list[int | None]) -> int | None:
    return sum(value for value in values if value is not None) if any(values) else None


def combine_parts(parts: dict[int, ProgressUpdate]) -> ProgressUpdate:
    """One progress for the job from the latest update of each parallel stream."""
    if len(parts) == 1:
        return next(iter(parts.values()))
    updates = list(parts.values())
    downloaded = _total([update.downloaded_bytes for update in updates])
    speeds = [update.speed for update in updates if update.speed is not None]
    etas = [update.eta for update in updates if update.eta is not None]
    total = None
    if all(update.total_bytes for update in updates):
        total = _total([update.total_bytes for update in updates])
    progress = None
    if downloaded is not None and total:
        progress = min(PERCENT, downloaded / total * PERCENT)
    return ProgressUpdate(
        downloaded_bytes=downloaded,
        total_bytes=total,
        speed=sum(speeds) if speeds else None,
        eta=max(etas) if etas else None,
        progress=progress,
    )


def _ffmpeg_progress(line: str) -> ProgressUpdate | None:
    """The size written so far, and the stream's data rate as the speed."""
    size = FFMPEG_PROGRESS.search(line)
    if size is None or size["unit"] not in UNIT_BYTES:
        return None
    bitrate = FFMPEG_BITRATE.search(line)
    speed = float(bitrate["kbits"]) * 1000 / 8 if bitrate else None
    downloaded = int(float(size["size"]) * UNIT_BYTES[size["unit"]])
    position = FFMPEG_TIME.search(line)
    media_seconds = None
    if position:
        minutes = int(position["hours"]) * 60 + int(position["minutes"])
        media_seconds = minutes * 60 + float(position["seconds"])
    return ProgressUpdate(downloaded, None, speed, None, None, media_seconds=media_seconds)


def parse_line(line: str) -> Update | None:
    line = PARALLEL_PREFIX.sub("", line, count=1)
    return _ffmpeg_progress(line) or _marker_update(line)


def _parse_progress(data: object) -> Update | None:
    return _progress(data) if isinstance(data, dict) else None


def _parse_info(data: object) -> Update | None:
    if not isinstance(data, dict):
        return None
    title = data.get("title")
    started = data.get("release_timestamp")
    return InfoUpdate(
        title=title if isinstance(title, str) else None,
        release_timestamp=float(started) if isinstance(started, int | float) else None,
    )


def _parse_file(data: object) -> Update | None:
    return FileUpdate(filepath=data) if isinstance(data, str) else None


def _parse_nfo(data: object) -> Update | None:
    return NfoUpdate(info=data) if isinstance(data, dict) else None


def _parse_chat(data: object) -> Update | None:
    if not isinstance(data, dict):
        return None
    filepath, url = data.get("filepath"), data.get("webpage_url")
    if not isinstance(filepath, str) or not isinstance(url, str):
        return None
    status = data.get("live_status")
    return ChatUpdate(filepath, url, status if isinstance(status, str) else None)


MARKER_PARSERS: dict[str, Callable[[object], Update | None]] = {
    PROGRESS_MARKER: _parse_progress,
    INFO_MARKER: _parse_info,
    FILE_MARKER: _parse_file,
    NFO_MARKER: _parse_nfo,
    CHAT_MARKER: _parse_chat,
}


def _marker_update(line: str) -> Update | None:
    for marker, parse in MARKER_PARSERS.items():
        if line.startswith(marker):
            try:
                return parse(json.loads(line.removeprefix(marker)))
            except json.JSONDecodeError:
                return None
    return None


def error_message(line: str) -> str | None:
    if line.startswith("ERROR:"):
        return line.removeprefix("ERROR:").strip()
    return None
