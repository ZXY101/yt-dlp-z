import time
from collections import defaultdict, deque


class FailureRateLimiter:
    """Blocks a key (client IP) after too many failures inside a sliding window.
    In-memory on purpose: the app is a single process."""

    def __init__(self, max_failures: int = 5, window_seconds: float = 60) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: defaultdict[str, deque[float]] = defaultdict(deque)

    def retry_after(self, key: str) -> int:
        """Seconds until the key may try again, 0 when not blocked."""
        failures = self._prune(key)
        if len(failures) < self.max_failures:
            return 0
        oldest = failures[0]
        return max(1, int(oldest + self.window_seconds - time.monotonic()) + 1)

    def record_failure(self, key: str) -> None:
        self._prune(key).append(time.monotonic())

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._failures.clear()
        else:
            self._failures.pop(key, None)

    def _prune(self, key: str) -> deque[float]:
        failures = self._failures[key]
        cutoff = time.monotonic() - self.window_seconds
        while failures and failures[0] < cutoff:
            failures.popleft()
        return failures
