"""Provider selection rules for the dialogue engine (env-driven)."""

import pytest

from app.core.config import Settings
from app.core.container import build_container
from app.providers.llm_dialogue import LLMDialogueEngine
from app.providers.mock_dialogue import MockDialogueEngine


def test_defaults_to_mock_engine():
    container = build_container(Settings())

    assert isinstance(container.engine, MockDialogueEngine)


def test_selects_llm_engine_when_configured():
    settings = Settings(engine_provider="llm", llm_api_key="test-key")

    container = build_container(settings)

    assert isinstance(container.engine, LLMDialogueEngine)


def test_rejects_llm_provider_without_api_key():
    settings = Settings(engine_provider="llm", llm_api_key="")

    with pytest.raises(ValueError, match="api key"):
        build_container(settings)


def test_rejects_unknown_provider():
    settings = Settings(engine_provider="magic")

    with pytest.raises(ValueError, match="ENGINE_PROVIDER"):
        build_container(settings)
