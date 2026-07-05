from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import settings


class SlidingWindowRateLimiter:
    """In-memory sliding-window limiter keyed by an arbitrary string.

    Suitable for single-process MVP deployments. A distributed setup would
    need a shared backend (for example Redis) instead of this local state.
    """

    def __init__(
        self,
        max_events: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        if self._max_events <= 0:
            return False
        now = self._clock()
        boundary = now - self._window_seconds
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= boundary:
                hits.popleft()
            if len(hits) >= self._max_events:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


booking_rate_limiter = SlidingWindowRateLimiter(
    max_events=settings.booking_rate_limit_max,
    window_seconds=settings.booking_rate_limit_window_seconds,
)


def get_booking_rate_limiter() -> SlidingWindowRateLimiter:
    return booking_rate_limiter


def client_ip(request: Request) -> str:
    client = request.client
    return client.host if client is not None else "unknown"
