import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable

from yt_dlp_z.schemas.media import MediaInfo

# Long enough to cover checking a link and then sending it; short enough that a stream
# that has since gone live is checked again.
PROBE_TTL_SECONDS = 300
MAX_ENTRIES = 200

ProbeKey = tuple[str, int | None, bool]


class ProbeCache:
    """Recent link checks, so sending a link that was just checked doesn't run yt-dlp
    again (2-7 s on YouTube). A check asked for while the same one runs waits for it.
    Failures aren't kept: the next try checks again."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._entries: OrderedDict[ProbeKey, tuple[float, MediaInfo]] = OrderedDict()
        self._running: dict[ProbeKey, asyncio.Task[MediaInfo]] = {}

    async def get_or_check(
        self, key: ProbeKey, check: Callable[[], Awaitable[MediaInfo]]
    ) -> MediaInfo:
        cached = self.get(key)
        if cached is not None:
            return cached
        task = self._running.get(key)
        if task is None:
            task = asyncio.ensure_future(self._check_and_keep(key, check))
            self._running[key] = task
        # Shielded: a caller giving up (closed popup) mustn't cancel the others' check.
        return await asyncio.shield(task)

    async def _check_and_keep(
        self, key: ProbeKey, check: Callable[[], Awaitable[MediaInfo]]
    ) -> MediaInfo:
        try:
            info = await check()
        finally:
            del self._running[key]
        self.put(key, info)
        return info

    def get(self, key: ProbeKey) -> MediaInfo | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        saved_at, info = entry
        if self._clock() - saved_at > PROBE_TTL_SECONDS:
            del self._entries[key]
            return None
        return info

    def put(self, key: ProbeKey, info: MediaInfo) -> None:
        self._entries[key] = (self._clock(), info)
        self._entries.move_to_end(key)
        while len(self._entries) > MAX_ENTRIES:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()
