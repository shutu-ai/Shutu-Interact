"""Voice loop endpoints: speech upload (ASR + reply) and TTS."""

import inspect

from app.api.routes import speech

UPLOAD = {"audio": ("speech.webm", b"fake-audio-bytes", "audio/webm")}


def _create_session(client) -> str:
    res = client.post(
        "/api/sessions", json={"age_group": "7-9", "topic": "animals"}
    )
    assert res.status_code == 200
    return res.json()["data"]["session_id"]


def test_speech_returns_transcript_and_next_turn(client):
    sid = _create_session(client)

    res = client.post(f"/api/sessions/{sid}/speech", files=UPLOAD)

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["transcript"] == "I like dogs."
    assert data["turn"] == 1
    assert data["finished"] is False
    assert data["assistant_text"]


def test_speech_unknown_session_404(client):
    res = client.post("/api/sessions/does-not-exist/speech", files=UPLOAD)

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "session_not_found"


def test_speech_asr_failed_on_empty_audio(client):
    sid = _create_session(client)

    res = client.post(
        f"/api/sessions/{sid}/speech",
        files={"audio": ("speech.webm", b"", "audio/webm")},
    )

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "asr_failed"


def test_tts_returns_wav_audio(client):
    res = client.post("/api/tts", json={"text": "Hello Coco"})

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/wav")
    assert res.content.startswith(b"RIFF")


def test_tts_rejects_blank_text(client):
    res = client.post("/api/tts", json={"text": "   "})

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


# --- G2: concurrency / lifecycle -----------------------------------------


def test_speech_route_runs_in_threadpool():
    """The speech handler must stay sync so uploads never block the event
    loop while ASR/LLM calls run (MVP-closure finding: async def + sync
    engine serialized every request under ENGINE_PROVIDER=llm)."""
    endpoint = next(
        route.endpoint
        for route in speech.router.routes
        if getattr(route, "path", "")
        == "/api/sessions/{session_id}/speech"
    )

    assert not inspect.iscoroutinefunction(endpoint)


def test_natural_finish_ends_server_session(client):
    """After the final finished turn the session is deleted server-side:
    a follow-up turn gets 404 and the kiosk restarts its flow."""
    sid = _create_session(client)

    finished = None
    for _ in range(4):  # greeting + 4 replies = MAX_TURNS(4) turns
        res = client.post(
            f"/api/sessions/{sid}/replies", json={"text": "I like dogs."}
        )
        assert res.status_code == 200
        finished = res.json()["data"]["finished"]
    assert finished is True

    follow_up = client.post(
        f"/api/sessions/{sid}/replies", json={"text": "one more"}
    )

    assert follow_up.status_code == 404
    assert follow_up.json()["error"]["code"] == "session_not_found"
