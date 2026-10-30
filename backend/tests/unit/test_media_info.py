from datetime import UTC, datetime, timedelta
from typing import Any

from yt_dlp_z.schemas.app_settings import DEFAULT_RECORDING
from yt_dlp_z.services.ytdlp.media import ENTRY_LIMIT, media_info, probe_args

NOW = datetime(2026, 10, 31, 12, tzinfo=UTC)


def info(data: dict[str, Any]) -> Any:
    return media_info(data, DEFAULT_RECORDING, NOW)


def test_a_plain_video() -> None:
    result = info(
        {
            "title": "A video",
            "uploader": "Someone",
            "thumbnail": "https://img.example/1.jpg",
            "extractor_key": "Vimeo",
            "duration": 61.5,
        }
    )
    assert result.kind == "video"
    assert (result.title, result.uploader, result.site) == ("A video", "Someone", "Vimeo")
    assert result.thumbnail == "https://img.example/1.jpg"
    assert result.duration == 61
    assert result.entry_count is None
    assert result.record_from_start is None


def test_playlist_count_comes_from_the_site() -> None:
    entries = [{"_type": "url"}] * 3
    result = info({"_type": "playlist", "playlist_count": 150, "entries": entries})
    assert (result.kind, result.entry_count) == ("playlist", 150)


def test_short_playlists_are_counted_and_full_pages_are_unknown() -> None:
    short = info({"_type": "playlist", "entries": [{"_type": "url"}] * 3})
    full = info({"_type": "playlist", "entries": [{"_type": "url"}] * ENTRY_LIMIT})
    assert (short.entry_count, full.entry_count) == (3, None)


def test_a_page_of_playlists_is_a_channel() -> None:
    tabs = [{"_type": "playlist", "title": "Videos"}, {"_type": "playlist", "title": "Live"}]
    assert info({"_type": "playlist", "entries": tabs}).kind == "channel"


def test_playlist_thumbnail_is_the_largest_listed() -> None:
    thumbnails = [{"url": "https://img.example/s.jpg"}, {}, {"url": "https://img.example/l.jpg"}]
    result = info({"_type": "playlist", "entries": [], "thumbnails": thumbnails})
    assert result.thumbnail == "https://img.example/l.jpg"


def test_upcoming_stream_reports_its_start() -> None:
    start = NOW + timedelta(days=1)
    result = info({"live_status": "is_upcoming", "release_timestamp": start.timestamp()})
    assert (result.kind, result.starts_at, result.live_since) == ("upcoming", start, None)
    assert result.record_from_start is True


def test_live_stream_follows_the_recording_settings() -> None:
    recent = info({"live_status": "is_live", "release_timestamp": NOW.timestamp() - 3600})
    old = info({"live_status": "is_live", "release_timestamp": NOW.timestamp() - 10 * 3600})
    assert recent.kind == "live"
    assert recent.live_since == NOW - timedelta(hours=1)
    assert (recent.record_from_start, old.record_from_start) == (True, False)


def test_finished_streams_are_videos_and_members_only_is_flagged() -> None:
    result = info({"live_status": "was_live", "availability": "subscriber_only"})
    assert (result.kind, result.members_only) == ("video", True)


def test_probe_args() -> None:
    assert probe_args(cookies=None, no_playlist=False) == [
        "--flat-playlist",
        "--playlist-items",
        f"1:{ENTRY_LIMIT}",
        "--ignore-no-formats-error",
    ]
    with_both = probe_args(cookies=None, no_playlist=True)
    assert with_both[-1] == "--no-playlist"
