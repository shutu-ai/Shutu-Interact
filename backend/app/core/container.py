"""Process-wide provider wiring for the API routes.

REPLACEMENT POINT: build_container chooses implementations from settings —
routes depend only on the protocols. Engine selection: ENGINE_PROVIDER=mock
(scripted, default) or llm (OpenAI-compatible endpoint via LLM_* settings).

The scripted mock always stays wired as fallback_engine (spec §8.3): any
LLM failure or guard trip swaps in a safe scripted turn.
"""

from dataclasses import dataclass

from app.core.config import Settings, load_settings
from app.providers.asr import (
    MockSpeechRecognizer,
    OpenAICompatibleTranscriber,
    SpeechRecognizer,
)
from app.providers.base import DialogueEngine
from app.providers.chat import OpenAIChatClient
from app.providers.llm_dialogue import LLMDialogueEngine
from app.providers.mock_dialogue import MockDialogueEngine
from app.providers.tts import MockSpeechSynthesizer, SpeechSynthesizer
from app.services.safety_guard import SafetyGuard
from app.services.session_manager import SessionManager


@dataclass
class Container:
    """Wiring holder, deliberately mutable so tests can swap providers."""

    engine: DialogueEngine
    manager: SessionManager
    asr: SpeechRecognizer
    tts: SpeechSynthesizer
    guard: SafetyGuard
    fallback_engine: DialogueEngine


def build_container(settings: Settings) -> Container:
    provider = settings.engine_provider
    if provider == "mock":
        engine: DialogueEngine = MockDialogueEngine()
    elif provider == "llm":
        if not settings.llm_api_key.strip():
            raise ValueError(
                "ENGINE_PROVIDER=llm requires an api key (set LLM_API_KEY)."
            )
        chat = OpenAIChatClient(
            api_base=settings.llm_api_base,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )
        engine = LLMDialogueEngine(chat=chat)
    else:
        raise ValueError(
            f"Unsupported ENGINE_PROVIDER: {provider!r} (use 'mock' or 'llm')."
        )

    asr_provider = settings.asr_provider
    if asr_provider == "mock":
        asr: SpeechRecognizer = MockSpeechRecognizer()
    elif asr_provider == "openai":
        if not settings.asr_api_key.strip():
            raise ValueError(
                "ASR_PROVIDER=openai requires an api key (set ASR_API_KEY)."
            )
        asr = OpenAICompatibleTranscriber(
            api_base=settings.asr_api_base,
            api_key=settings.asr_api_key,
            model=settings.asr_model,
            timeout_seconds=settings.asr_timeout_seconds,
        )
    else:
        raise ValueError(
            f"Unsupported ASR_PROVIDER: {asr_provider!r} (use 'mock' or 'openai')."
        )

    return Container(
        engine=engine,
        manager=SessionManager(
            ttl_seconds=settings.session_ttl_seconds,
            max_duration_seconds=settings.session_max_seconds,
        ),
        asr=asr,
        tts=MockSpeechSynthesizer(),
        guard=SafetyGuard(),
        fallback_engine=MockDialogueEngine(),
    )


container = build_container(load_settings())
