"""Shared guard wiring for the session/speech routes (plan §5).

Output side: any unsafe engine text is swapped for a scripted reply.
Input side: unsafe child text never reaches the engine or the stored
history — the scripted engine gives a gentle on-topic redirect instead.

Logs carry session id + anonymous reason category only, never the
flagged text itself (spec §7.3).
"""

import logging

from app.models.dialogue import Session, Turn
from app.providers.base import DialogueEngine
from app.services.safety_guard import SafetyGuard

logger = logging.getLogger(__name__)


def check_input(session_id: str, text: str, guard: SafetyGuard) -> bool:
    """True when the child text is safe to forward and store."""
    result = guard.check_input(text)
    if not result.ok:
        logger.warning(
            "input_guarded reason=%s session_id=%s", result.reason, session_id
        )
    return result.ok


def guarded_start(
    session: Session,
    engine: DialogueEngine,
    fallback_engine: DialogueEngine,
    guard: SafetyGuard,
) -> Turn:
    """Greeting turn with the output guard applied."""
    turn = engine.start(session.age_group, session.topic)
    result = guard.check_output(turn.assistant_text)
    if result.ok:
        return turn
    logger.warning(
        "output_guarded reason=%s session_id=%s", result.reason, session.session_id
    )
    return fallback_engine.start(session.age_group, session.topic)


def guarded_respond(
    session: Session,
    text: str,
    engine: DialogueEngine,
    fallback_engine: DialogueEngine,
    guard: SafetyGuard,
) -> Turn:
    """Reply turn with the output guard applied."""
    turn = engine.respond(session, text)
    result = guard.check_output(turn.assistant_text)
    if result.ok:
        return turn
    logger.warning(
        "output_guarded reason=%s session_id=%s", result.reason, session.session_id
    )
    return fallback_engine.respond(session, text)
