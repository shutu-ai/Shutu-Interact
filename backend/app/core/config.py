"""Application settings, loaded from environment variables (.env)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "coco-english"
    session_ttl_seconds: int = 600
    engine_provider: str = "mock"  # "mock" | "llm"
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    # Comma-separated origins the kiosk frontend may call from ("*" for the
    # LAN MVP); tighten in production (e.g. "https://kiosk.example.com").
    cors_allow_origins: tuple[str, ...] = ("*",)


def _parse_origins(raw: str) -> tuple[str, ...]:
    parts = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    return parts or ("*",)


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "coco-english"),
        session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "600")),
        engine_provider=os.getenv("ENGINE_PROVIDER", "mock"),
        llm_api_base=os.getenv("LLM_API_BASE", "https://api.openai.com/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        cors_allow_origins=_parse_origins(
            os.getenv("CORS_ALLOW_ORIGINS", "*")
        ),
    )


settings = load_settings()
