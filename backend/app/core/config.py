"""Application settings, loaded from environment variables (.env)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "coco-english"
    session_ttl_seconds: int = 600
    # Total lifetime cap for one session (~180s); <= 0 disables the cap.
    session_max_seconds: float | None = 180.0
    engine_provider: str = "mock"  # "mock" | "llm"
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    asr_provider: str = "mock"  # "mock" | "openai"
    asr_api_base: str = "https://api.openai.com/v1"
    asr_api_key: str = ""
    asr_model: str = "whisper-1"
    asr_timeout_seconds: float = 10.0
    # Comma-separated origins the kiosk frontend may call from ("*" for the
    # LAN MVP); tighten in production (e.g. "https://kiosk.example.com").
    cors_allow_origins: tuple[str, ...] = ("*",)


def _parse_origins(raw: str) -> tuple[str, ...]:
    parts = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    return parts or ("*",)


def _parse_duration_cap(raw: str) -> float | None:
    value = float(raw)
    return value if value > 0 else None


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "coco-english"),
        session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "600")),
        session_max_seconds=_parse_duration_cap(
            os.getenv("SESSION_MAX_SECONDS", "180")
        ),
        engine_provider=os.getenv("ENGINE_PROVIDER", "mock"),
        llm_api_base=os.getenv("LLM_API_BASE", "https://api.openai.com/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        asr_provider=os.getenv("ASR_PROVIDER", "mock"),
        asr_api_base=os.getenv("ASR_API_BASE", "https://api.openai.com/v1"),
        asr_api_key=os.getenv("ASR_API_KEY", ""),
        asr_model=os.getenv("ASR_MODEL", "whisper-1"),
        asr_timeout_seconds=float(os.getenv("ASR_TIMEOUT_SECONDS", "10.0")),
        cors_allow_origins=_parse_origins(
            os.getenv("CORS_ALLOW_ORIGINS", "*")
        ),
    )


settings = load_settings()
