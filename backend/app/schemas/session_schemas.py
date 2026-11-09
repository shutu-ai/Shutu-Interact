"""Request schemas and the uniform API response envelope.

Envelope contract (frozen in Task 1):
  success -> 200 {"success": true, "data": {...}}
  error   -> 4xx {"success": false, "error": {"code", "message"}}
"""

from typing import Any

from pydantic import BaseModel, field_validator

from app.models.dialogue import AGE_GROUPS, TOPICS, Turn


def ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, "data": data}


def err(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message}}


def turn_to_data(turn: Turn) -> dict[str, Any]:
    return {
        "assistant_text": turn.assistant_text,
        "state": turn.state,
        "turn": turn.turn,
        "finished": turn.finished,
    }


class CreateSessionRequest(BaseModel):
    age_group: str
    topic: str

    @field_validator("age_group")
    @classmethod
    def _age_group_allowed(cls, value: str) -> str:
        if value not in AGE_GROUPS:
            raise ValueError(f"age_group must be one of {AGE_GROUPS}")
        return value

    @field_validator("topic")
    @classmethod
    def _topic_allowed(cls, value: str) -> str:
        if value not in TOPICS:
            raise ValueError(f"topic must be one of {TOPICS}")
        return value


class ReplyRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be empty")
        return stripped
