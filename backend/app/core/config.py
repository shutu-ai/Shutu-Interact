"""Application settings, loaded from environment variables (.env in Task 7)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "coco-english"
    session_ttl_seconds: int = 600


def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "coco-english"),
        session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "600")),
    )


settings = load_settings()
