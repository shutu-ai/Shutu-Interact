"""Session lifecycle routes: create, reply, end.

MVP wiring: providers come from app.core.container. REPLACEMENT POINT:
swap MockDialogueEngine for the controlled LLM engine (Task 4) there —
the DialogueEngine protocol stays identical. Guard wiring (plan §5):
unsafe engine output → scripted fallback; unsafe child input → gentle
redirect without persisting the text.
"""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.routes.guarding import check_input, guarded_respond, guarded_start
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
    greeting = guarded_start(
        session,
        container.engine,
        container.fallback_engine,
        container.guard,
    )
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

    if not check_input(session_id, payload.text, container.guard):
        turn = container.fallback_engine.respond(session, payload.text)
        container.manager.append_turn(session_id, turn)
        return ok(turn_to_data(turn))

    container.manager.append_child_text(session_id, payload.text)
    session = container.manager.get(session_id)
    turn = guarded_respond(
        session,
        payload.text,
        container.engine,
        container.fallback_engine,
        container.guard,
    )
    container.manager.append_turn(session_id, turn)
    return ok(turn_to_data(turn))


@router.post("/api/sessions/{session_id}/end")
def end_session(session_id: str) -> Any:
    try:
        container.manager.end(session_id)
    except SessionNotFoundError:
        return JSONResponse(status_code=404, content=_SESSION_NOT_FOUND)
    return ok({"ended": True})
