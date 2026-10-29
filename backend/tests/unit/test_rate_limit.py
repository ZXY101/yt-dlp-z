import pytest

from yt_dlp_z.core.rate_limit import FailureRateLimiter


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    now = [1000.0]
    monkeypatch.setattr("yt_dlp_z.core.rate_limit.time.monotonic", lambda: now[0])
    return now


def test_blocks_after_max_failures(clock: list[float]) -> None:
    limiter = FailureRateLimiter(max_failures=2, window_seconds=60)
    limiter.record_failure("ip")
    assert limiter.retry_after("ip") == 0
    limiter.record_failure("ip")
    assert limiter.retry_after("ip") == 61


def test_failures_expire_after_window(clock: list[float]) -> None:
    limiter = FailureRateLimiter(max_failures=1, window_seconds=60)
    limiter.record_failure("ip")
    clock[0] += 61
    assert limiter.retry_after("ip") == 0


def test_reset_one_key_or_all(clock: list[float]) -> None:
    limiter = FailureRateLimiter(max_failures=1, window_seconds=60)
    limiter.record_failure("a")
    limiter.record_failure("b")
    limiter.reset("a")
    assert limiter.retry_after("a") == 0
    assert limiter.retry_after("b") > 0
    limiter.reset()
    assert limiter.retry_after("b") == 0
