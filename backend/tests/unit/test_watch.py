from datetime import UTC, date, datetime, timedelta

import pytest

from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.schemas.subscriptions import ContentType, SubscriptionFilters
from yt_dlp_z.services.watch.channel import ChannelError, channel_from_info, channel_url
from yt_dlp_z.services.watch.feed import FeedError, feed_url, parse_feed
from yt_dlp_z.services.watch.filters import skip_reason
from yt_dlp_z.services.watch.probe import VideoInfo, info_from_json
from yt_dlp_z.services.watch.streams import sweep_due
from yt_dlp_z.services.watch.watcher import is_due

ATOM = (
    '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">'
    "<entry><yt:videoId>new</yt:videoId><title>New &amp; shiny</title>"
    "<published>2026-10-02T10:00:00+00:00</published></entry>"
    "<entry><title>no id</title></entry>"
    "<entry><yt:videoId>old</yt:videoId><published>not a date</published></entry>"
    "</feed>"
)
NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


def video(**changes: object) -> VideoInfo:
    values: dict[str, object] = {
        "title": "A video",
        "content_type": ContentType.VIDEO,
        "live_status": "not_live",
        "duration": 600,
        "release_at": None,
        "members_only": False,
    }
    return VideoInfo(**{**values, **changes})  # type: ignore[arg-type]


def test_parse_feed_keeps_order_and_skips_entries_without_an_id() -> None:
    entries = parse_feed(ATOM.encode())
    assert [entry.video_id for entry in entries] == ["new", "old"]
    assert entries[0].title == "New & shiny"
    assert entries[0].published_at == datetime(2026, 10, 2, 10, tzinfo=UTC)
    assert entries[1].title == "old"
    assert entries[1].published_at is None


def test_parse_feed_rejects_invalid_xml() -> None:
    with pytest.raises(FeedError, match="isn't valid XML"):
        parse_feed(b"<feed>")


def test_feed_url_fills_in_the_channel() -> None:
    assert feed_url("https://x/feed?c={channel_id}", "UC1") == "https://x/feed?c=UC1"


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"live_status": "is_upcoming"}, ContentType.STREAM),
        ({"live_status": "was_live", "media_type": "short"}, ContentType.STREAM),
        ({"media_type": "short"}, ContentType.SHORT),
        ({"webpage_url": "https://www.youtube.com/shorts/abc"}, ContentType.SHORT),
        ({"media_type": "video"}, ContentType.VIDEO),
    ],
)
def test_content_type_from_probe(data: dict[str, object], expected: ContentType) -> None:
    assert info_from_json(data).content_type is expected


def test_probe_fields() -> None:
    info = info_from_json(
        {
            "title": "Stream",
            "duration": 61.5,
            "release_timestamp": 0,
            "availability": "subscriber_only",
        }
    )
    assert info.title == "Stream"
    assert info.duration == 61
    assert info.release_at == datetime(1970, 1, 1, tzinfo=UTC)
    assert info.members_only is True
    assert info_from_json({"title": 3}).title is None


@pytest.mark.parametrize(
    ("filters", "info", "title", "reason"),
    [
        ({}, video(), "x", None),
        ({}, video(content_type=ContentType.SHORT), "x", "It's a Short"),
        ({}, video(content_type=ContentType.STREAM), "x", "It's a live stream or premiere"),
        ({}, video(members_only=True), "x", "Members-only"),
        ({"include_members_only": True}, video(members_only=True), "x", None),
        ({"title_include": "^part"}, video(), "PART 2", None),
        ({"title_include": "^part"}, video(), "x", "The title doesn't match the include filter"),
        ({"title_exclude": "trailer"}, video(), "Trailer!", "The title matches the exclude filter"),
        ({"min_duration": 601}, video(), "x", "Shorter than the minimum duration"),
        ({"max_duration": 599}, video(), "x", "Longer than the maximum duration"),
        ({"max_duration": 1}, video(duration=None), "x", None),
    ],
)
def test_skip_reason(
    filters: dict[str, object], info: VideoInfo, title: str, reason: str | None
) -> None:
    parsed = SubscriptionFilters.model_validate(filters)
    assert skip_reason(parsed, info, title, None) == reason


def test_published_after_filter() -> None:
    filters = SubscriptionFilters(published_after=date(2026, 10, 2))
    early = datetime(2026, 10, 1, 23, tzinfo=UTC)
    assert skip_reason(filters, video(), "x", early) == "Published before 2026-10-02"
    assert skip_reason(filters, video(), "x", early + timedelta(hours=1)) is None
    assert skip_reason(filters, video(), "x", None) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("@someone", "https://www.youtube.com/@someone"),
        (" https://m.youtube.com/@someone ", "https://m.youtube.com/@someone"),
        ("https://youtube.com/channel/UC1", "https://youtube.com/channel/UC1"),
    ],
)
def test_channel_url(raw: str, expected: str) -> None:
    assert channel_url(raw) == expected


@pytest.mark.parametrize("raw", ["someone", "ftp://youtube.com/@x", "https://evil.example/@x"])
def test_channel_url_rejects_other_sites(raw: str) -> None:
    with pytest.raises(ChannelError):
        channel_url(raw)


def test_channel_from_info_falls_back_sensibly() -> None:
    channel = channel_from_info({"id": "UCabc", "title": "Abc - Videos"})
    assert channel.channel_id == "UCabc"
    assert channel.name == "Abc - Videos"
    assert channel.url == "https://www.youtube.com/channel/UCabc"
    assert channel_from_info({"channel_id": "UCx"}).name == "UCx"
    with pytest.raises(ChannelError):
        channel_from_info({"id": "PLplaylist"})


def test_is_due() -> None:
    assert is_due(None, 10, 0.0, NOW)
    assert is_due(NOW - timedelta(minutes=10), 10, 0.0, NOW)
    assert not is_due(NOW - timedelta(minutes=9), 10, 0.0, NOW)
    assert not is_due(NOW - timedelta(minutes=10), 10, 0.1, NOW)
    # SQLite hands back naive datetimes; they are UTC.
    assert is_due((NOW - timedelta(minutes=11)).replace(tzinfo=None), 10, 0.0, NOW)


def test_streams_sweep_runs_every_30_minutes_for_stream_subscriptions() -> None:
    now = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    streams = {"content_types": ["video", "stream"]}
    assert sweep_due(Subscription(filters=streams, streams_checked_at=None), now)
    recent = now - timedelta(minutes=29)
    assert not sweep_due(Subscription(filters=streams, streams_checked_at=recent), now)
    # SQLite hands back naive datetimes; they are UTC.
    old = (now - timedelta(minutes=30)).replace(tzinfo=None)
    assert sweep_due(Subscription(filters=streams, streams_checked_at=old), now)
    assert not sweep_due(Subscription(filters={"content_types": ["video"]}), now)
