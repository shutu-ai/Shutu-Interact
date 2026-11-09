"""Session lifecycle routes: create, reply, end.

MVP wiring: providers come from app.core.container. REPLACEMENT POINT:
swap MockDialogueEngine for the controlled LLM engine (Task 4) there —
the DialogueEngine protocol stays identical.
"""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.container import container
from app.models.dialogue import MAX_TURNS
from app.schemas.session_schemas import (
    CreateSessionRequest,
    ReplyRequest,
    err,
    ok,
    turn_to_data,
)
from app.services.session_manager import SessionNotFoundError

router = APIRouter()

_SESSION_NOT_FOUND = err(
    "session_not_found", "Session not found or already ended."
)


@router.post("/api/sessions")
def create_session(payload: CreateSessionRequest) -> dict[str, Any]:
    session = container.manager.create(payload.age_group, payload.topic)
    greeting = container.engine.start(session.age_group, session.topic)
    container.manager.append_turn(session.session_id, greeting)
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
        session = container.manager.get(session_id)
    except SessionNotFoundError:
        return JSONResponse(status_code=404, content=_SESSION_NOT_FOUND)

    turn = container.engine.respond(session, payload.text)
    container.manager.append_turn(session_id, turn)
    return ok(turn_to_data(turn))


@router.post("/api/sessions/{session_id}/end")
def end_session(session_id: str) -> Any:
    try:
        container.manager.end(session_id)
    except SessionNotFoundError:
        return JSONResponse(status_code=404, content=_SESSION_NOT_FOUND)
    return ok({"ended": True})
