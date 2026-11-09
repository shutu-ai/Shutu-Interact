"""In-memory session storage for the MVP (no database, plan §10).

Sessions are removed on end() and expire after ttl_seconds (spec §8.3:
会话结束必须清理上下文) — context never outlives the session. An expired
session answers 404 so the kiosk restarts its flow with a fresh one.
"""

import time
import uuid
from dataclasses import replace

from app.models.dialogue import Session, Turn


class SessionNotFoundError(KeyError):
    """Raised when a session id does not exist (or was already ended)."""


class SessionManager:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, Session] = {}

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
        if time.time() - session.created_at >= self._ttl_seconds:
            del self._sessions[session_id]
            raise SessionNotFoundError(session_id)
        return session

    def append_turn(self, session_id: str, turn: Turn) -> Session:
        session = self.get(session_id)
        updated = replace(session, turns=session.turns + (turn,))
        self._sessions[session_id] = updated
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
        """Drop every session past its TTL; returns how many were removed."""
        now = time.time()
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if now - session.created_at >= self._ttl_seconds
        ]
        for session_id in expired:
            del self._sessions[session_id]
        return len(expired)
