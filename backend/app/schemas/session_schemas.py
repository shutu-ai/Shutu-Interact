"""Request schemas and the uniform API response envelope.

Envelope contract (frozen in Task 1):
  success -> 200 {"success": true, "data": {...}}
  error   -> 4xx {"success": false, "error": {"code", "message"}}
"""

from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, field_validator

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


def _not_blank(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("text must not be empty")
    return stripped


NotBlankText = Annotated[str, AfterValidator(_not_blank)]


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
    text: NotBlankText


class TtsRequest(BaseModel):
    text: NotBlankText
