"""Session TTL cleanup: expired sessions disappear (spec §5.1D, §8.3)."""

import time

import pytest

import app.services.session_manager as session_manager_module
from app.core.config import Settings
from app.core.container import build_container
from app.services.session_manager import SessionManager, SessionNotFoundError


class _ShiftedClock:
    """``time`` replacement returning real time shifted into the future."""

    def __init__(self, offset_seconds: float) -> None:
        self._offset = offset_seconds

    def time(self) -> float:
        return time.time() + self._offset


def test_expired_session_is_not_found() -> None:
    manager = SessionManager(ttl_seconds=0)
    session = manager.create("7-9", "animals")

    with pytest.raises(SessionNotFoundError):
        manager.get(session.session_id)


def test_fresh_session_is_served() -> None:
    manager = SessionManager(ttl_seconds=600)
    session = manager.create("7-9", "animals")

    assert manager.get(session.session_id).session_id == session.session_id


def test_purge_expired_returns_removed_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = SessionManager(ttl_seconds=600)
    manager.create("4-6", "colors")
    manager.create("10-12", "sports")
    monkeypatch.setattr(
        session_manager_module, "time", _ShiftedClock(offset_seconds=700)
    )

    assert manager.purge_expired() == 2
    assert manager.purge_expired() == 0  # nothing left to remove


def test_purge_keeps_fresh_sessions() -> None:
    manager = SessionManager(ttl_seconds=600)
    session = manager.create("7-9", "hobbies")

    assert manager.purge_expired() == 0
    assert manager.get(session.session_id).session_id == session.session_id


def test_expired_sessions_are_swept_on_next_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = SessionManager(ttl_seconds=600)
    old = manager.create("4-6", "colors")
    monkeypatch.setattr(
        session_manager_module, "time", _ShiftedClock(offset_seconds=700)
    )

    manager.create("10-12", "sports")

    with pytest.raises(SessionNotFoundError):
        manager.get(old.session_id)


def test_container_manager_serves_fresh_session() -> None:
    container = build_container(Settings())
    session = container.manager.create("7-9", "animals")

    assert container.manager.get(session.session_id).session_id == (
        session.session_id
    )
