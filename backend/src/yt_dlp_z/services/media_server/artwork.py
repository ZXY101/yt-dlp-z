"""The channel's picture and banner for media servers, in the channel folder next to
tvshow.nfo: poster.jpg (the channel picture), fanart.jpg (the whole banner image, 16:9,
used as the backdrop) and banner.jpg (the banner strip). Fetched once per channel; never
overwritten, so a picture the user put there stays.
"""

import asyncio
import logging
import urllib.request
from pathlib import Path
from typing import Any

from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30
MAX_IMAGE_BYTES = 20_000_000
ARTWORK = ("poster.jpg", "fanart.jpg", "banner.jpg")
# Wider than this (width / height) is the banner strip YouTube shows above a channel.
STRIP_RATIO = 4

# Channel folders being fetched for, so parallel downloads fetch only once.
_fetching: set[Path] = set()
# Running fetches; kept so they aren't garbage-collected before they finish.
_tasks: set[asyncio.Task[None]] = set()


def _sized(thumbnails: list[dict[str, Any]]) -> list[tuple[int, int, str]]:
    sized = []
    for item in thumbnails:
        width, height, url = item.get("width"), item.get("height"), item.get("url")
        if isinstance(width, int) and isinstance(height, int) and height and isinstance(url, str):
            sized.append((width, height, url))
    return sized


def _by_id(thumbnails: list[dict[str, Any]], thumbnail_id: str) -> str | None:
    url = next((item.get("url") for item in thumbnails if item.get("id") == thumbnail_id), None)
    return url if isinstance(url, str) else None


def pick_artwork(thumbnails: list[dict[str, Any]]) -> dict[str, str]:
    """File name → image URL, for the pictures the channel has. yt-dlp lists the channel
    picture in several sizes (square) and the banner as strips plus the whole image."""
    sized = _sized(thumbnails)
    squares = [entry for entry in sized if entry[0] == entry[1]]
    strips = [entry for entry in sized if entry[0] > STRIP_RATIO * entry[1]]
    found = {
        "poster.jpg": max(squares)[2] if squares else _by_id(thumbnails, "avatar_uncropped"),
        "fanart.jpg": _by_id(thumbnails, "banner_uncropped"),
        "banner.jpg": max(strips)[2] if strips else None,
    }
    return {name: url for name, url in found.items() if url is not None}


def _download(url: str) -> bytes:
    if not url.startswith("https://"):
        raise ValueError(f"Not an https URL: {url}")
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
        data: bytes = response.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("The image is too large")
    return data


def missing_artwork(show_dir: Path) -> bool:
    return not all((show_dir / name).exists() for name in ARTWORK)


async def _channel_thumbnails(ytdlp_command: list[str], channel_id: str) -> list[dict[str, Any]]:
    url = f"https://www.youtube.com/channel/{channel_id}"
    data = await run_ytdlp_json(ytdlp_command, ["--flat-playlist", "--playlist-items", "0"], url)
    thumbnails = data.get("thumbnails")
    return thumbnails if isinstance(thumbnails, list) else []


async def fetch_channel_artwork(ytdlp_command: list[str], channel_id: str, show_dir: Path) -> None:
    if show_dir in _fetching or not missing_artwork(show_dir):
        return
    _fetching.add(show_dir)
    try:
        thumbnails = await _channel_thumbnails(ytdlp_command, channel_id)
        for name, url in pick_artwork(thumbnails).items():
            target = show_dir / name
            if not target.exists():
                target.write_bytes(await asyncio.to_thread(_download, url))
    except (YtdlpJsonError, OSError, ValueError) as error:
        logger.warning("Couldn't fetch the channel artwork for %s: %s", show_dir.name, error)
    finally:
        _fetching.discard(show_dir)


def start_artwork_fetch(ytdlp_command: list[str], channel_id: str, show_dir: Path) -> None:
    """Fetches in the background, so the download that found the folder doesn't wait."""
    if show_dir in _fetching or not missing_artwork(show_dir):
        return
    task = asyncio.create_task(fetch_channel_artwork(ytdlp_command, channel_id, show_dir))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
