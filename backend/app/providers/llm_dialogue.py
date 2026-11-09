"""LLM-backed dialogue engine with a scripted fallback.

Control flow (turn budget, finish praise) is deterministic; the LLM only
produces wording. Any LLM failure (network, HTTP, parse) falls back to
the scripted engine so the kiosk loop never dead-ends (spec §8.3).
"""

import logging

from app.models.dialogue import (
    MAX_TURNS,
    STATE_GREETING,
    STATE_LISTENING,
    STATE_PRAISE,
    Session,
    Turn,
)
from app.providers.base import DialogueEngine
from app.providers.chat import ChatClient
from app.providers.mock_dialogue import FINISH_PRAISE, MockDialogueEngine
from app.providers.prompts import build_system_prompt

_logger = logging.getLogger(__name__)


class LLMDialogueEngine:
    def __init__(
        self,
        chat: ChatClient,
        fallback: DialogueEngine | None = None,
    ) -> None:
        self._chat = chat
        self._fallback = fallback if fallback is not None else MockDialogueEngine()

    def start(self, age_group: str, topic: str) -> Turn:
        prompt = build_system_prompt(age_group, topic, MAX_TURNS)
        try:
            text = self._chat.complete(prompt, [])
        except Exception:  # any failure falls back to the scripted engine
            _logger.warning(
                "LLM greeting failed; using scripted fallback", exc_info=True
            )
            return self._fallback.start(age_group, topic)
        return Turn(
            assistant_text=text, state=STATE_GREETING, turn=0, finished=False
        )

    def respond(self, session: Session, child_text: str) -> Turn:
        last = session.last
        if last is None:
            raise ValueError("Session has no greeting turn; it is uninitialized.")
        if last.finished:
            return last

        next_index = last.turn + 1
        if next_index >= MAX_TURNS:
            return Turn(
                assistant_text=FINISH_PRAISE,
                state=STATE_PRAISE,
                turn=MAX_TURNS,
                finished=True,
            )

        prompt = build_system_prompt(session.age_group, session.topic, MAX_TURNS)
        history = self._build_history(session, child_text)
        try:
            text = self._chat.complete(prompt, history)
        except Exception:  # any failure falls back to the scripted engine
            _logger.warning(
                "LLM reply failed; using scripted fallback", exc_info=True
            )
            return self._fallback.respond(session, child_text)
        return Turn(
            assistant_text=text,
            state=STATE_LISTENING,
            turn=next_index,
            finished=False,
        )

    @staticmethod
    def _build_history(
        session: Session, child_text: str
    ) -> list[dict[str, str]]:
        """Alternating [assistant/user] history ending with the child's line."""
        history: list[dict[str, str]] = []
        for index, turn in enumerate(session.turns):
            if index > 0 and index - 1 < len(session.child_texts):
                history.append(
                    {"role": "user", "content": session.child_texts[index - 1]}
                )
            history.append({"role": "assistant", "content": turn.assistant_text})
        history.append({"role": "user", "content": child_text})
        return history
