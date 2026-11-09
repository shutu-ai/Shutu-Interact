"""Route-level guard wiring: unsafe input/output handled, errors enveloped.

Plan §5: output side → scripted fallback reply; input side → gentle
redirect without persisting the unsafe text; crashes → error envelope;
logs carry reasons only, never child text.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.core.container import container
from app.main import app
from app.models.dialogue import STATE_LISTENING, Session, Turn
from app.providers.base import DialogueEngine
from app.providers.mock_dialogue import MockDialogueEngine
from app.services.session_manager import SessionManager

AUDIO = {"audio": ("speech.webm", b"fake-audio-bytes", "audio/webm")}


def _create_session(topic: str) -> str:
    res = client.post(
        "/api/sessions", json={"age_group": "7-9", "topic": topic}
    )
    assert res.status_code == 200
    return res.json()["data"]["session_id"]


class _ScriptedEngine:
    """Engine double that always answers with one fixed text."""

    def __init__(self, text: str) -> None:
        self._text = text
        self.calls = 0

    def start(self, age_group: str, topic: str) -> Turn:
        self.calls += 1
        return Turn(assistant_text=self._text, state=STATE_LISTENING,
                    turn=0, finished=False)

    def respond(self, session: Session, child_text: str) -> Turn:
        self.calls += 1
        return Turn(assistant_text=self._text, state=STATE_LISTENING,
                    turn=len(session.turns), finished=False)


class _BoomEngine:
    """Engine double that always crashes."""

    def start(self, age_group: str, topic: str) -> Turn:
        raise RuntimeError("llm exploded")

    def respond(self, session: Session, child_text: str) -> Turn:
        raise RuntimeError("llm exploded")


client = TestClient(app)


def test_create_replaces_unsafe_greeting(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = _ScriptedEngine("What is your name, little one?")
    monkeypatch.setattr(container, "engine", bad)

    res = client.post(
        "/api/sessions", json={"age_group": "4-6", "topic": "animals"}
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["assistant_text"] != "What is your name, little one?"
    expected = MockDialogueEngine().start("4-6", "animals")
    assert data["assistant_text"] == expected.assistant_text


def test_reply_replaces_unsafe_engine_output(client: TestClient,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    sid = _create_session("animals")
    snapshot = container.manager.get(sid)
    bad = _ScriptedEngine("What is your name?")
    monkeypatch.setattr(container, "engine", bad)

    res = client.post(f"/api/sessions/{sid}/replies",
                      json={"text": "I like dogs!"})

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["assistant_text"] != "What is your name?"
    expected = MockDialogueEngine().respond(snapshot, "I like dogs!")
    assert data["assistant_text"] == expected.assistant_text
    assert data["finished"] is False


def test_reply_redirects_unsafe_child_input(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    sid = _create_session("colors")
    snapshot = container.manager.get(sid)
    engine = _ScriptedEngine("Guns are fun, let's talk weapons!")
    monkeypatch.setattr(container, "engine", engine)

    with caplog.at_level(logging.WARNING):
        res = client.post(f"/api/sessions/{sid}/replies",
                          json={"text": "i have a gun"})

    assert res.status_code == 200
    data = res.json()["data"]
    assert engine.calls == 0  # unsafe text never reaches the dialogue engine
    expected = MockDialogueEngine().respond(snapshot, "i have a gun")
    assert data["assistant_text"] == expected.assistant_text
    # Unsafe child text is never persisted, but a placeholder keeps the
    # turns/child_texts pairing aligned for the LLM engine's history.
    texts = container.manager.get(sid).child_texts
    assert texts == ("[redacted]",)
    assert "gun" not in "".join(texts)
    assert "input_guarded" in caplog.text
    assert "gun" not in caplog.text  # transcript itself is never logged


def test_speech_replaces_unsafe_engine_output(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sid = _create_session("sports")
    snapshot = container.manager.get(sid)
    bad = _ScriptedEngine("How much money do you have?")
    monkeypatch.setattr(container, "engine", bad)

    res = client.post(f"/api/sessions/{sid}/speech", files=AUDIO)

    assert res.status_code == 200
    data = res.json()["data"]
    assert "transcript" not in data  # G3: no child-text echo
    expected = MockDialogueEngine().respond(snapshot, "I like dogs.")
    assert data["assistant_text"] == expected.assistant_text


def test_speech_redirects_unsafe_transcript(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _ScriptedAsr:
        def transcribe(self, audio: bytes, content_type: str) -> str:
            return "i have a gun"

    sid = _create_session("hobbies")
    snapshot = container.manager.get(sid)
    engine = _ScriptedEngine("Secrets between us, okay?")
    monkeypatch.setattr(container, "asr", _ScriptedAsr())
    monkeypatch.setattr(container, "engine", engine)

    res = client.post(f"/api/sessions/{sid}/speech", files=AUDIO)

    assert res.status_code == 200
    data = res.json()["data"]
    assert "transcript" not in data  # G3: flagged child text is never echoed
    assert engine.calls == 0
    expected = MockDialogueEngine().respond(snapshot, "i have a gun")
    assert data["assistant_text"] == expected.assistant_text
    texts = container.manager.get(sid).child_texts
    assert texts == ("[redacted]",)
    assert "gun" not in "".join(texts)


def test_engine_crash_returns_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sid = _create_session("fruits")
    monkeypatch.setattr(container, "engine", _BoomEngine())
    raw_client = TestClient(app, raise_server_exceptions=False)

    res = raw_client.post(f"/api/sessions/{sid}/replies",
                          json={"text": "hello"})

    assert res.status_code == 500
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "internal_error"


def test_expired_session_reply_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    expired_manager = SessionManager(ttl_seconds=0)
    monkeypatch.setattr(container, "manager", expired_manager)
    session = expired_manager.create("7-9", "animals")

    res = client.post(f"/api/sessions/{session.session_id}/replies",
                      json={"text": "hi"})

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "session_not_found"
