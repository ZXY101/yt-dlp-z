import asyncio

import pytest

from yt_dlp_z.schemas.media import MediaInfo
from yt_dlp_z.services.ytdlp.probe_cache import MAX_ENTRIES, PROBE_TTL_SECONDS, ProbeCache


def info(title: str) -> MediaInfo:
    return MediaInfo(
        kind="video",
        title=title,
        uploader=None,
        thumbnail=None,
        site=None,
        duration=None,
        entry_count=None,
        starts_at=None,
        live_since=None,
        members_only=False,
    )


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_an_answer_is_reused_until_it_expires() -> None:
    clock = Clock()
    cache = ProbeCache(clock)
    key = ("https://example.com/a", None, False)
    cache.put(key, info("A"))
    clock.now += PROBE_TTL_SECONDS
    assert cache.get(key) == info("A")
    clock.now += 1
    assert cache.get(key) is None


def test_cookies_and_playlist_choice_are_part_of_the_key() -> None:
    cache = ProbeCache()
    cache.put(("https://example.com/a", None, False), info("A"))
    assert cache.get(("https://example.com/a", 1, False)) is None
    assert cache.get(("https://example.com/a", None, True)) is None


def test_the_oldest_answers_are_dropped_when_full() -> None:
    cache = ProbeCache()
    for number in range(MAX_ENTRIES + 1):
        cache.put((f"https://example.com/{number}", None, False), info(str(number)))
    assert cache.get(("https://example.com/0", None, False)) is None
    assert cache.get(("https://example.com/1", None, False)) is not None


def test_clear_forgets_everything() -> None:
    cache = ProbeCache()
    cache.put(("https://example.com/a", None, False), info("A"))
    cache.clear()
    assert cache.get(("https://example.com/a", None, False)) is None


async def test_checks_of_the_same_link_share_one_run() -> None:
    cache = ProbeCache()
    runs: list[str] = []
    release = asyncio.Event()

    async def check() -> MediaInfo:
        runs.append("run")
        await release.wait()
        return info("A")

    key = ("https://example.com/a", None, False)
    first = asyncio.create_task(cache.get_or_check(key, check))
    second = asyncio.create_task(cache.get_or_check(key, check))
    await asyncio.sleep(0)
    release.set()
    assert await first == await second == info("A")
    assert runs == ["run"]
    assert await cache.get_or_check(key, check) == info("A")
    assert runs == ["run"]


async def test_a_failed_check_is_not_kept() -> None:
    cache = ProbeCache()
    key = ("https://example.com/a", None, False)

    async def failing() -> MediaInfo:
        raise ValueError("unavailable")

    with pytest.raises(ValueError, match="unavailable"):
        await cache.get_or_check(key, failing)
    assert cache.get(key) is None
