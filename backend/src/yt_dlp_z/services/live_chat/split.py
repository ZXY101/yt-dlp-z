"""Turns a recording's captured chat into one .live_chat.json per saved part.

The capture runs for the whole recording, in its own folder, and can be several files when
it had to restart. Comments are placed by YouTube's own timestamps, so a part's overlay stays
in sync whatever happened between parts: each line gets the time into that part's video, in the
form yt-dlp writes for live chat, so a rebuild reads it like any other chat file.
"""

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from yt_dlp_z.core.config import Settings
from yt_dlp_z.services.live_chat.overlay import CHAT_SUFFIX

PARTIAL_SUFFIX = ".part"
MS_PER_SECOND = 1000
US_PER_MS = 1000


@dataclass(frozen=True)
class SavedPart:
    """A recording part's file, and when (epoch seconds) the moment at its 0:00 was live."""

    video: Path
    started: float


def capture_dir(settings: Settings, job_id: int) -> Path:
    return settings.config_dir / "live-chat" / f"job-{job_id}"


def capture_files(folder: Path) -> list[Path]:
    """One per capture run: finished, or with yt-dlp's .part name if it was stopped. Not the
    fragment and state files yt-dlp keeps beside those while it runs."""
    wanted = (CHAT_SUFFIX, CHAT_SUFFIX + PARTIAL_SUFFIX)
    return sorted(path for path in folder.glob("chat-*") if path.name.endswith(wanted))


def discard_capture(settings: Settings, job_id: int) -> None:
    shutil.rmtree(capture_dir(settings, job_id), ignore_errors=True)


def _chat_item(entry: dict[str, Any]) -> dict[str, Any]:
    """The action's item, whichever renderer it is: {"id": …, "timestampUsec": …}."""
    actions = entry["replayChatItemAction"]["actions"]
    item = actions[0].get("addChatItemAction", {}).get("item", {})
    return next(iter(item.values()), {})


def _read_lines(paths: list[Path]) -> list[tuple[int, dict[str, Any]]]:
    """Every comment once, as (milliseconds, entry), oldest first. A capture that restarted
    gets some of the same comments again; the end of a stopped file can be half a line."""
    seen: set[str] = set()
    lines: list[tuple[int, dict[str, Any]]] = []
    for path in paths:
        with path.open(encoding="utf-8") as chat_file:
            for line in chat_file:
                try:
                    entry = json.loads(line)
                    item = _chat_item(entry)
                    moment, item_id = int(item["timestampUsec"]) // US_PER_MS, item.get("id")
                except (ValueError, TypeError, KeyError, IndexError, AttributeError):
                    continue
                if item_id is None or item_id not in seen:
                    seen.add(str(item_id))
                    lines.append((moment, entry))
    lines.sort(key=lambda pair: pair[0])
    return lines


def _part_at(parts: list[SavedPart], moment_ms: int) -> SavedPart:
    """The last part started by then. Waiting-room chat goes in the first, with a negative
    time, so it's kept in the JSON but never shown."""
    current = parts[0]
    for part in parts:
        if part.started * MS_PER_SECOND <= moment_ms:
            current = part
    return current


def split_capture(folder: Path, parts: list[SavedPart]) -> list[Path]:
    """Writes each part's chat beside its video and returns the files that have comments."""
    if not parts:
        return []
    ordered = sorted(parts, key=lambda part: part.started)
    outputs: dict[Path, TextIO] = {}
    try:
        for moment, entry in _read_lines(capture_files(folder)):
            part = _part_at(ordered, moment)
            target = part.video.with_name(part.video.stem + CHAT_SUFFIX + ".tmp")
            if target not in outputs:
                outputs[target] = target.open("w", encoding="utf-8")
            entry["videoOffsetTimeMsec"] = str(moment - round(part.started * MS_PER_SECOND))
            outputs[target].write(json.dumps(entry, ensure_ascii=False) + "\n")
    finally:
        for output in outputs.values():
            output.close()
    finished = []
    for temporary in outputs:
        final = temporary.with_name(temporary.name.removesuffix(".tmp"))
        os.replace(temporary, final)
        finished.append(final)
    return finished
