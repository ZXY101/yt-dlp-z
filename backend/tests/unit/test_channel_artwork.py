import asyncio
from pathlib import Path
from typing import Any

import pytest

from yt_dlp_z.services.media_server import artwork

# Shaped like yt-dlp's answer for a channel (sizes from a real one).
THUMBNAILS: list[dict[str, Any]] = [
    {"id": "0", "url": "https://img/strip-1060", "width": 1060, "height": 175},
    {"id": "5", "url": "https://img/strip-2560", "width": 2560, "height": 424},
    {"id": "banner_uncropped", "url": "https://img/banner"},
    {"id": "7", "url": "https://img/avatar-900", "width": 900, "height": 900},
    {"id": "avatar_uncropped", "url": "https://img/avatar"},
]


def test_picks_the_largest_picture_and_the_whole_banner() -> None:
    assert artwork.pick_artwork(THUMBNAILS) == {
        "poster.jpg": "https://img/avatar-900",
        "fanart.jpg": "https://img/banner",
        "banner.jpg": "https://img/strip-2560",
    }


def test_falls_back_to_what_the_channel_has() -> None:
    assert artwork.pick_artwork([{"id": "avatar_uncropped", "url": "https://img/a"}]) == {
        "poster.jpg": "https://img/a"
    }
    assert artwork.pick_artwork([{"id": "0", "url": "https://img/x"}]) == {}


def fake_channel(monkeypatch: pytest.MonkeyPatch, thumbnails: list[dict[str, Any]]) -> list[str]:
    fetched: list[str] = []

    async def channel_thumbnails(_command: list[str], _channel_id: str) -> list[dict[str, Any]]:
        return thumbnails

    def download(url: str) -> bytes:
        fetched.append(url)
        return url.encode()

    monkeypatch.setattr(artwork, "_channel_thumbnails", channel_thumbnails)
    monkeypatch.setattr(artwork, "_download", download)
    return fetched


def test_writes_the_artwork_once_and_keeps_existing_pictures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetched = fake_channel(monkeypatch, THUMBNAILS)
    (tmp_path / "poster.jpg").write_bytes(b"mine")
    asyncio.run(artwork.fetch_channel_artwork(["yt-dlp"], "UC1", tmp_path))
    assert (tmp_path / "poster.jpg").read_bytes() == b"mine"
    assert (tmp_path / "fanart.jpg").read_bytes() == b"https://img/banner"
    assert (tmp_path / "banner.jpg").read_bytes() == b"https://img/strip-2560"
    assert fetched == ["https://img/banner", "https://img/strip-2560"]

    asyncio.run(artwork.fetch_channel_artwork(["yt-dlp"], "UC1", tmp_path))
    assert len(fetched) == 2  # nothing missing any more


def test_a_failure_is_only_logged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_channel(monkeypatch, THUMBNAILS)

    def broken(_url: str) -> bytes:
        raise OSError("connection reset")

    monkeypatch.setattr(artwork, "_download", broken)
    asyncio.run(artwork.fetch_channel_artwork(["yt-dlp"], "UC1", tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_only_https_images_are_fetched() -> None:
    with pytest.raises(ValueError, match="https"):
        artwork._download("file:///etc/passwd")
