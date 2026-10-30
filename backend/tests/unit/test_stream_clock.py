from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from yt_dlp_z.services.live.stream_clock import StreamClock
from yt_dlp_z.services.ytdlp.output import ProgressUpdate


def progress(part: int, fragments: tuple[int, int] | None) -> ProgressUpdate:
    return ProgressUpdate(None, None, None, None, None, part=part, fragments=fragments)


def test_from_the_start_it_counts_fragments() -> None:
    # Live for 10 h with 7200 fragments: each fragment is 5 s.
    clock = StreamClock((datetime.now(UTC) - timedelta(hours=10)).replace(tzinfo=None))
    clock.update(progress(0, (720, 7200)))
    clock.update(progress(1, (1440, 7200)))
    # Audio (720 fragments, 1 h) is furthest behind, so 1 h of the stream is saved.
    assert abs(clock.seconds() - 3600) < 5


def test_from_now_it_counts_time() -> None:
    with patch("yt_dlp_z.services.live.stream_clock.time.monotonic", return_value=100.0):
        clock = StreamClock(None)
    clock.update(progress(0, (720, 7200)))
    with patch("yt_dlp_z.services.live.stream_clock.time.monotonic", return_value=130.0):
        assert clock.seconds() == 30.0


def test_without_fragment_numbers_it_counts_time() -> None:
    clock = StreamClock(datetime.now(UTC) - timedelta(hours=10))
    clock.update(progress(0, None))
    clock.update(progress(0, (0, 0)))
    assert clock.seconds() < 5
