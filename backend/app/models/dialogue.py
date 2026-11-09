"""Domain constants and immutable dialogue models."""

from dataclasses import dataclass
from typing import Tuple

AGE_GROUPS: Tuple[str, ...] = ("4-6", "7-9", "10-12")
TOPICS: Tuple[str, ...] = ("animals", "colors", "fruits", "sports", "hobbies")
MAX_TURNS: int = 4

STATE_GREETING: str = "greeting"
STATE_LISTENING: str = "listening"
STATE_PRAISE: str = "praise"


@dataclass(frozen=True)
class Turn:
    """One assistant turn. Never mutated; new turns are new objects."""

    assistant_text: str
    state: str
    turn: int
    finished: bool


@dataclass(frozen=True)
class Session:
    """A dialogue session. State changes produce a new Session instance."""

    session_id: str
    age_group: str
    topic: str
    turns: Tuple[Turn, ...] = ()

    @property
    def last(self) -> Turn | None:
        return self.turns[-1] if self.turns else None
