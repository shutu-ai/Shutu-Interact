"""In-memory session storage for the MVP (no database, plan §10).

Sessions are removed on end(); context never outlives the session
(spec §8.3: 会话结束必须清理上下文).
"""

import uuid
from dataclasses import replace

from app.models.dialogue import Session, Turn


class SessionNotFoundError(KeyError):
    """Raised when a session id does not exist (or was already ended)."""


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, age_group: str, topic: str) -> Session:
        session = Session(
            session_id=uuid.uuid4().hex, age_group=age_group, topic=topic
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise SessionNotFoundError(session_id) from exc

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
