"""Reads a channel's RSS (Atom) feed: cheap, needs no API key, lists the newest 15 uploads."""

import asyncio
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

FEED_TIMEOUT_SECONDS = 30
MAX_FEED_BYTES = 2_000_000
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


class FeedError(Exception):
    pass


@dataclass(frozen=True)
class FeedEntry:
    video_id: str
    title: str
    published_at: datetime | None


def _published(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def parse_feed(content: bytes) -> list[FeedEntry]:
    """Entries newest first, as YouTube lists them."""
    try:
        root = ET.fromstring(content)  # noqa: S314  (Python's expat guards against entity bombs)
    except ET.ParseError as error:
        raise FeedError(f"The channel feed isn't valid XML: {error}") from error
    entries = []
    for entry in root.findall("atom:entry", NAMESPACES):
        video_id = entry.findtext("yt:videoId", namespaces=NAMESPACES)
        if not video_id:
            continue
        title = entry.findtext("atom:title", default=video_id, namespaces=NAMESPACES)
        published = _published(entry.findtext("atom:published", namespaces=NAMESPACES))
        entries.append(FeedEntry(video_id=video_id, title=title, published_at=published))
    return entries


def feed_url(template: str, channel_id: str) -> str:
    return template.replace("{channel_id}", channel_id)


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "yt-dlp-z"})  # noqa: S310
    with urllib.request.urlopen(request, timeout=FEED_TIMEOUT_SECONDS) as response:  # noqa: S310
        content: bytes = response.read(MAX_FEED_BYTES)
        return content


async def fetch_feed(url: str) -> list[FeedEntry]:
    try:
        content = await asyncio.to_thread(_download, url)
    except OSError as error:
        raise FeedError(f"Couldn't load the channel feed: {error}") from error
    return parse_feed(content)
