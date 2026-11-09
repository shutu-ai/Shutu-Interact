"""In-memory session storage for the MVP (no database, plan §10).

Sessions are removed on end() and expire after ttl_seconds (spec §8.3:
会话结束必须清理上下文) — context never outlives the session. A total
duration cap (max_duration_seconds, default ~180s) bounds how long any
single session can live even if the child keeps interacting. An expired
or capped session answers 404 so the kiosk restarts its flow. A natural
finish (a turn with finished=True) deletes the session immediately.
"""

import time
import uuid
from dataclasses import replace

from app.models.dialogue import Session, Turn


class SessionNotFoundError(KeyError):
    """Raised when a session id does not exist (or was already ended)."""


class SessionManager:
    def __init__(
        self,
        ttl_seconds: int = 600,
        max_duration_seconds: float | None = 180.0,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_duration_seconds = max_duration_seconds
        self._sessions: dict[str, Session] = {}

    def _is_expired(self, elapsed_seconds: float) -> bool:
        if elapsed_seconds >= self._ttl_seconds:
            return True
        return (
            self._max_duration_seconds is not None
            and elapsed_seconds >= self._max_duration_seconds
        )

    def create(self, age_group: str, topic: str) -> Session:
        self.purge_expired()
        session = Session(
            session_id=uuid.uuid4().hex, age_group=age_group, topic=topic
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        if self._is_expired(time.time() - session.created_at):
            del self._sessions[session_id]
            raise SessionNotFoundError(session_id)
        return session

    def append_turn(self, session_id: str, turn: Turn) -> Session:
        session = self.get(session_id)
        updated = replace(session, turns=session.turns + (turn,))
        self._sessions[session_id] = updated
        if turn.finished:
            # Natural finish: the dialogue is over — delete the session now
            # instead of waiting out the TTL (spec §8.3 cleanup).
            del self._sessions[session_id]
        return updated

    def append_child_text(self, session_id: str, child_text: str) -> Session:
        """Record the child's utterance so the engine keeps real history."""
        session = self.get(session_id)
        updated = replace(session, child_texts=session.child_texts + (child_text,))
        self._sessions[session_id] = updated
        return updated

    def end(self, session_id: str) -> None:
        """Delete the session and all of its context."""
        self.get(session_id)  # raises SessionNotFoundError when unknown
        del self._sessions[session_id]

    def purge_expired(self) -> int:
        """Drop every session past its TTL or duration cap; returns how
        many were removed."""
        now = time.time()
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_expired(now - session.created_at)
        ]
        for session_id in expired:
            del self._sessions[session_id]
        return len(expired)
