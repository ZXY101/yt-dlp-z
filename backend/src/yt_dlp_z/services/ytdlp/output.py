"""Parses the marker lines yt-dlp prints for yt-dlp-z (see command.py)."""

import json
import re
from dataclasses import dataclass
from typing import Any

from yt_dlp_z.services.ytdlp.command import FILE_MARKER, INFO_MARKER, PROGRESS_MARKER

PERCENT = 100
# When yt-dlp downloads several streams at once (live-from-start recordings fetch video and
# audio in parallel), it prefixes each progress line with the stream's number: "1: …".
PARALLEL_PREFIX = re.compile(r"^\d+: ")


@dataclass(frozen=True)
class ProgressUpdate:
    downloaded_bytes: int | None
    total_bytes: int | None
    speed: float | None
    eta: int | None
    progress: float | None
    # Which of several parallel streams this is about (yt-dlp's progress_idx).
    part: int = 0


@dataclass(frozen=True)
class InfoUpdate:
    title: str | None


@dataclass(frozen=True)
class FileUpdate:
    filepath: str


Update = ProgressUpdate | InfoUpdate | FileUpdate


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
    return ProgressUpdate(
        downloaded_bytes=int(downloaded) if downloaded is not None else None,
        total_bytes=int(total) if total is not None else None,
        speed=_number(data, "speed"),
        eta=int(eta) if eta is not None else None,
        progress=percent,
        part=part if isinstance(part, int) else 0,
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


def parse_line(line: str) -> Update | None:
    line = PARALLEL_PREFIX.sub("", line, count=1)
    try:
        if line.startswith(PROGRESS_MARKER):
            data = json.loads(line.removeprefix(PROGRESS_MARKER))
            return _progress(data) if isinstance(data, dict) else None
        if line.startswith(INFO_MARKER):
            data = json.loads(line.removeprefix(INFO_MARKER))
            if not isinstance(data, dict):
                return None
            title = data.get("title")
            return InfoUpdate(title=title if isinstance(title, str) else None)
        if line.startswith(FILE_MARKER):
            path = json.loads(line.removeprefix(FILE_MARKER))
            return FileUpdate(filepath=path) if isinstance(path, str) else None
    except json.JSONDecodeError:
        return None
    return None


def error_message(line: str) -> str | None:
    if line.startswith("ERROR:"):
        return line.removeprefix("ERROR:").strip()
    return None
