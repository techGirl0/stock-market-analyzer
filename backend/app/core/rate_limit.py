from collections import defaultdict
from threading import Lock
from time import monotonic

from app.core.errors import BackendError


class FixedWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = monotonic()
        with self._lock:
            started, count = self._hits[key]
            if now - started >= self.window_seconds:
                started, count = now, 0
            if count >= self.limit:
                raise BackendError(
                    "rate_limited",
                    "Too many requests. Try again later.",
                    429,
                    {"retry_after_seconds": max(1, int(self.window_seconds - (now - started)))},
                )
            self._hits[key] = (started, count + 1)


auth_limiter = FixedWindowLimiter(limit=30, window_seconds=60)

# Per-user budget for the LLM-backed research endpoints (SCRUM-69). LLM calls
# are the most expensive requests in the API, so authenticated users get a
# stricter limit than the global per-IP API limiter.
research_limiter = FixedWindowLimiter(limit=10, window_seconds=60)
