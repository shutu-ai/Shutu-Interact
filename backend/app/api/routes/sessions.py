"""Session lifecycle routes: create, reply, end.

MVP wiring: one process-wide engine + manager instance. REPLACEMENT POINT:
swap MockDialogueEngine for the controlled LLM engine (Task 4) here — the
DialogueEngine protocol stays identical.
"""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.dialogue import MAX_TURNS
from app.providers.base import DialogueEngine
from app.providers.mock_dialogue import MockDialogueEngine
from app.schemas.session_schemas import (
    CreateSessionRequest,
    ReplyRequest,
    err,
    ok,
    turn_to_data,
)
from app.services.session_manager import SessionManager, SessionNotFoundError

router = APIRouter()

engine: DialogueEngine = MockDialogueEngine()
manager = SessionManager()

_SESSION_NOT_FOUND = err(
    "session_not_found", "Session not found or already ended."
)


@router.post("/api/sessions")
def create_session(payload: CreateSessionRequest) -> dict[str, Any]:
    session = manager.create(payload.age_group, payload.topic)
    greeting = engine.start(session.age_group, session.topic)
    manager.append_turn(session.session_id, greeting)
    return ok(
        {
            "session_id": session.session_id,
            **turn_to_data(greeting),
            "max_turns": MAX_TURNS,
        }
    )


@router.post("/api/sessions/{session_id}/replies")
def reply(session_id: str, payload: ReplyRequest) -> Any:
    try:
        session = manager.get(session_id)
    except SessionNotFoundError:
        return JSONResponse(status_code=404, content=_SESSION_NOT_FOUND)

    turn = engine.respond(session, payload.text)
    manager.append_turn(session_id, turn)
    return ok(turn_to_data(turn))


@router.post("/api/sessions/{session_id}/end")
def end_session(session_id: str) -> Any:
    try:
        manager.end(session_id)
    except SessionNotFoundError:
        return JSONResponse(status_code=404, content=_SESSION_NOT_FOUND)
    return ok({"ended": True})
