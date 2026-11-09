"""Voice loop routes: speech upload (ASR + dialogue turn) and TTS.

半双工 loop (spec §6.5): child speaks → upload → ASR → engine turn →
frontend plays the reply. One round-trip keeps latency inside the ≤3s
budget (spec §8.2). Guard wiring (plan §5): unsafe transcripts are
gently redirected without reaching the engine or the stored history.
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


@router.post("/api/sessions/{session_id}/speech")
async def speech(session_id: str, audio: UploadFile) -> Any:
    raw = await audio.read()
    content_type = audio.content_type or "application/octet-stream"

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
        return ok({"transcript": transcript, **turn_to_data(turn)})

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
    return ok({"transcript": transcript, **turn_to_data(turn)})


@router.post("/api/tts")
def tts(payload: TtsRequest) -> Response:
    audio = container.tts.synthesize(payload.text.strip())
    return Response(content=audio, media_type="audio/wav")
