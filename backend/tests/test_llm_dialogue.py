"""LLMDialogueEngine: LLM wording, deterministic control flow, fallback."""

import pytest

from app.models.dialogue import MAX_TURNS, STATE_GREETING, STATE_LISTENING, STATE_PRAISE
from app.providers.llm_dialogue import LLMDialogueEngine
from app.providers.mock_dialogue import MockDialogueEngine


class FakeChat:
    """Deterministic ChatClient double that records its calls."""

    def __init__(self, replies: list[str] | None = None, error: Exception | None = None):
        self.calls: list[tuple[str, list[dict[str, str]]]] = []
        self.replies = replies or [
            "Hello! I'm Coco! Let's talk about animals! Do you like dogs?"
        ]
        self.error = error

    def complete(self, system_prompt: str, history: list[dict[str, str]]) -> str:
        self.calls.append((system_prompt, history))
        if self.error is not None:
            raise self.error
        index = min(len(self.calls) - 1, len(self.replies) - 1)
        return self.replies[index]


def _engine_with_session(chat: FakeChat):
    engine = LLMDialogueEngine(chat=chat)
    session_id = "test-session"
    from app.models.dialogue import Session

    greeting = engine.start("7-9", "animals")
    session = Session(
        session_id=session_id,
        age_group="7-9",
        topic="animals",
        turns=(greeting,),
        child_texts=(),
    )
    return engine, session


def test_start_returns_greeting_turn_from_llm():
    chat = FakeChat()
    engine = LLMDialogueEngine(chat=chat)

    turn = engine.start("7-9", "animals")

    assert turn.turn == 0
    assert turn.state == STATE_GREETING
    assert turn.finished is False
    assert turn.assistant_text == (
        "Hello! I'm Coco! Let's talk about animals! Do you like dogs?"
    )
    assert len(chat.calls) == 1


def test_respond_sends_history_and_returns_llm_turn():
    chat = FakeChat(replies=["Great job! Do you have a pet?"])
    engine, session = _engine_with_session(chat)

    turn = engine.respond(session, "I like dogs")

    assert turn.turn == 1
    assert turn.state == STATE_LISTENING
    assert turn.finished is False
    assert turn.assistant_text == "Great job! Do you have a pet?"

    system_prompt, history = chat.calls[-1]
    assert system_prompt.startswith("You are Coco")
    assert history[-1] == {"role": "user", "content": "I like dogs"}
    assert {"role": "assistant", "content": session.turns[0].assistant_text} in history


def test_final_turn_returns_scripted_praise_without_llm_call():
    chat = FakeChat()
    engine, session = _engine_with_session(chat)

    last = session.last
    assert last is not None
    from dataclasses import replace

    at_limit = replace(
        session,
        turns=session.turns + tuple(
            last if i == 0 else type(last)(
                assistant_text=f"turn {i}", state=STATE_LISTENING, turn=i, finished=False
            )
            for i in range(1, MAX_TURNS)
        ),
        child_texts=("a", "b", "c"),
    )
    calls_before = len(chat.calls)

    turn = engine.respond(at_limit, "one more")

    assert turn.finished is True
    assert turn.state == STATE_PRAISE
    assert turn.turn == MAX_TURNS
    assert len(chat.calls) == calls_before


def test_finished_session_is_idempotent_without_llm_call():
    chat = FakeChat()
    engine, session = _engine_with_session(chat)
    from dataclasses import replace

    from app.models.dialogue import Turn

    finished = replace(
        session,
        turns=session.turns
        + (
            Turn(
                assistant_text="Amazing talking with you!",
                state=STATE_PRAISE,
                turn=MAX_TURNS,
                finished=True,
            ),
        ),
    )
    calls_before = len(chat.calls)

    turn = engine.respond(finished, "hello again")

    assert turn.finished is True
    assert len(chat.calls) == calls_before


def test_llm_failure_falls_back_to_scripted_engine():
    chat = FakeChat(error=RuntimeError("LLM unreachable"))
    engine = LLMDialogueEngine(chat=chat)

    greeting = engine.start("4-6", "animals")
    assert greeting.turn == 0
    assert greeting.assistant_text  # scripted greeting text

    from app.models.dialogue import Session

    session = Session(
        session_id="s",
        age_group="4-6",
        topic="animals",
        turns=(greeting,),
        child_texts=(),
    )
    reply_turn = engine.respond(session, "dog")

    assert reply_turn.turn == 1
    assert reply_turn.assistant_text  # scripted praise + question


def test_engine_uses_scripted_fallback_instance():
    chat = FakeChat(error=RuntimeError("down"))
    engine = LLMDialogueEngine(chat=chat)

    assert isinstance(engine._fallback, MockDialogueEngine)  # noqa: SLF001


@pytest.mark.parametrize("group,topic", [("4-6", "colors"), ("10-12", "hobbies")])
def test_respond_works_across_age_groups_and_topics(group: str, topic: str):
    chat = FakeChat(replies=["Nice! One more?"])
    engine = LLMDialogueEngine(chat=chat)
    from app.models.dialogue import Session

    greeting = engine.start(group, topic)
    session = Session(
        session_id="s", age_group=group, topic=topic, turns=(greeting,), child_texts=()
    )

    turn = engine.respond(session, "hello")

    assert turn.turn == 1
    assert turn.assistant_text == "Nice! One more?"
