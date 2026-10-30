"""Measures how much of a stream a recording part has saved."""

import time
from datetime import UTC, datetime

from yt_dlp_z.services.ytdlp.output import ProgressUpdate


def as_utc(moment: datetime) -> datetime:
    """SQLite drops the timezone; stored values are UTC."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


class StreamClock:
    """Seconds of the stream a part has saved.

    Recording from now, that's the time the part has run. Recording an already-live stream
    from its start, yt-dlp downloads faster than real time, so it's worked out from fragment
    numbers instead: the newest fragment's number covers the whole time the stream has been
    live, so each fragment is (time live) / (newest fragment's number) seconds long.
    """

    def __init__(self, live_since: datetime | None) -> None:
        """`live_since`: when the stream went live, for parts recorded from its start."""
        self._live_since = as_utc(live_since) if live_since is not None else None
        self._started = time.monotonic()
        # Seconds saved by each parallel stream (video, audio).
        self._saved: dict[int, float] = {}

    def update(self, update: ProgressUpdate) -> None:
        if self._live_since is None or update.fragments is None:
            return
        saved, newest = update.fragments
        if newest > 0:
            live_for = (datetime.now(UTC) - self._live_since).total_seconds()
            self._saved[update.part] = saved * live_for / newest

    def seconds(self) -> float:
        if not self._saved:
            return time.monotonic() - self._started
        # The stream furthest behind decides what the file holds.
        return min(self._saved.values())
