"""Provider protocols — replaceable adapters (plan §6.4).

Every voice/AI capability is a Protocol so implementations can be swapped
without touching route or service code.
"""

from typing import Protocol

from app.models.dialogue import Session, Turn


class DialogueEngine(Protocol):
    """Produces the assistant's turns for a session."""

    def start(self, age_group: str, topic: str) -> Turn:
        """Return the greeting turn that opens a new session."""
        ...

    def respond(self, session: Session, child_text: str) -> Turn:
        """Return the assistant's next turn after the child's reply."""
        ...
