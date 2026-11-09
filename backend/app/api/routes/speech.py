"""Voice loop routes: speech upload (ASR + dialogue turn) and TTS.

半双工 loop (spec §6.5): child speaks → upload → ASR → engine turn →
frontend plays the reply. One round-trip keeps latency inside the ≤3s
budget (spec §8.2). Guard wiring (plan §5): unsafe transcripts are
gently redirected without reaching the engine or the stored history.
G3 (MVP closure): uploads are size/type bounded, turns are rate
limited per session, and the child transcript is never echoed back to
the client — the reply line is all the kiosk needs.
"""

from typing import Any

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse, Response

from app.api.routes.guarding import check_input, guarded_respond
from app.core.container import container
from app.schemas.session_schemas import TtsRequest, err, ok, turn_to_data
from app.services.session_manager import SessionNotFoundError

router = APIRouter()

_SESSION_NOT_FOUND = err(
    "session_not_found", "Session not found or already ended."
)
_ASR_FAILED = err(
    "asr_failed", "Speech recognition failed. Please try again."
)
_AUDIO_TOO_LARGE = err(
    "audio_too_large", "That recording is too long. Please try a shorter one."
)
_UNSUPPORTED_AUDIO = err(
    "unsupported_audio", "That audio format is not supported."
)
_RATE_LIMITED = err(
    "rate_limited", "Too many turns too quickly. Please wait a moment."
)


@router.post("/api/sessions/{session_id}/speech")
def speech(session_id: str, audio: UploadFile) -> Any:
    # Sync handler: FastAPI runs it in the threadpool, so the blocking ASR
    # call never stalls the event loop for concurrent kiosk requests.
    if not container.limiter.allow(session_id):
        return JSONResponse(status_code=429, content=_RATE_LIMITED)

    content_type = audio.content_type or "application/octet-stream"
    if not content_type.split(";")[0].strip().lower().startswith("audio/"):
        return JSONResponse(status_code=415, content=_UNSUPPORTED_AUDIO)

    # Read one byte beyond the cap so oversized payloads are detected
    # without ever holding unbounded audio in memory.
    raw = audio.file.read(container.max_upload_bytes + 1)
    if len(raw) > container.max_upload_bytes:
        return JSONResponse(status_code=413, content=_AUDIO_TOO_LARGE)

    try:
        session = container.manager.get(session_id)
    except SessionNotFoundError:
        return JSONResponse(status_code=404, content=_SESSION_NOT_FOUND)

    transcript = container.asr.transcribe(raw, content_type).strip()
    if not transcript:
        return JSONResponse(status_code=422, content=_ASR_FAILED)

    if not check_input(session_id, transcript, container.guard):
        # Placeholder keeps turns/child_texts count-aligned for the LLM
        # engine's history pairing; the flagged text itself is never stored.
        container.manager.append_child_text(session_id, "[redacted]")
        turn = container.fallback_engine.respond(session, transcript)
        container.manager.append_turn(session_id, turn)
        return ok(turn_to_data(turn))

    container.manager.append_child_text(session_id, transcript)
    session = container.manager.get(session_id)
    turn = guarded_respond(
        session,
        transcript,
        container.engine,
        container.fallback_engine,
        container.guard,
    )
    container.manager.append_turn(session_id, turn)
    return ok(turn_to_data(turn))


@router.post("/api/tts")
def tts(payload: TtsRequest) -> Response:
    audio = container.tts.synthesize(payload.text.strip())
    return Response(content=audio, media_type="audio/wav")
