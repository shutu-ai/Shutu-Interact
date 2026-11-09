"""Per-key sliding-window rate limiting (G3, MVP closure).

In-memory, per-process: good enough for the single-kiosk MVP. The
limiter counts attempts, not successes — failed or 404 turns still
consume budget so a runaway client cannot bypass it by breaking things.
Keys carry no content; only timestamps are stored, never text.
"""

import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self, max_events: int, window_seconds: float = 60.0) -> None:
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Record one attempt for `key` and say whether it fits the window."""
        now = time.time()
        events = self._events[key]
        horizon = now - self._window_seconds
        while events and events[0] <= horizon:
            events.popleft()
        if len(events) >= self._max_events:
            return False
        events.append(now)
        return True
