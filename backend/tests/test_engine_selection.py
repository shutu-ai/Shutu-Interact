"""Provider selection rules for the dialogue engine (env-driven)."""

import pytest

from app.core.config import Settings, load_settings
from app.core.container import build_container
from app.core import container as container_module
from app.providers.chat import OpenAIChatClient
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


def test_llm_timeout_defaults_to_six_seconds():
    settings = Settings()

    assert settings.llm_timeout_seconds == 6.0


def test_load_settings_reads_llm_timeout_from_env(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "15")

    assert load_settings().llm_timeout_seconds == 15.0


def test_llm_timeout_flows_into_chat_client(monkeypatch):
    captured: dict = {}
    real_client = container_module.OpenAIChatClient

    def spy_client(**kwargs):
        captured.update(kwargs)
        return real_client(**kwargs)

    monkeypatch.setattr(container_module, "OpenAIChatClient", spy_client)

    build_container(
        Settings(
            engine_provider="llm",
            llm_api_key="test-key",
            llm_timeout_seconds=15.0,
        )
    )

    assert captured["timeout_seconds"] == 15.0
