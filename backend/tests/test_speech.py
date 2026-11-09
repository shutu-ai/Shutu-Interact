"""Voice loop endpoints: speech upload (ASR + reply) and TTS."""

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
