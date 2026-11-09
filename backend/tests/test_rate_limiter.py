"""G3 (MVP closure): per-session sliding-window rate limiting."""

import time

import pytest

import app.services.rate_limiter as rate_limiter_module
from app.services.rate_limiter import SlidingWindowRateLimiter


class _ShiftedClock:
    """``time`` replacement returning real time shifted into the future."""

    def __init__(self, offset_seconds: float) -> None:
        self._offset = offset_seconds

    def time(self) -> float:
        return time.time() + self._offset


def test_allows_up_to_the_limit_then_denies() -> None:
    limiter = SlidingWindowRateLimiter(max_events=3, window_seconds=60.0)

    assert limiter.allow("sid-1") is True
    assert limiter.allow("sid-1") is True
    assert limiter.allow("sid-1") is True
    assert limiter.allow("sid-1") is False  # burst #4 denied


def test_window_slides_and_budget_returns(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = SlidingWindowRateLimiter(max_events=2, window_seconds=60.0)
    limiter.allow("sid-1")
    limiter.allow("sid-1")
    assert limiter.allow("sid-1") is False

    monkeypatch.setattr(
        rate_limiter_module, "time", _ShiftedClock(offset_seconds=61.0)
    )

    assert limiter.allow("sid-1") is True


def test_keys_are_independent() -> None:
    limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60.0)
    limiter.allow("sid-1")

    assert limiter.allow("sid-2") is True
    assert limiter.allow("sid-1") is False
