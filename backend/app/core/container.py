"""Process-wide provider wiring for the API routes.

REPLACEMENT POINT: build_container chooses implementations from settings —
routes depend only on the protocols. Engine selection: ENGINE_PROVIDER=mock
(scripted, default) or llm (OpenAI-compatible endpoint via LLM_* settings).
"""

from dataclasses import dataclass

from app.core.config import Settings, load_settings
from app.providers.asr import MockSpeechRecognizer, SpeechRecognizer
from app.providers.base import DialogueEngine
from app.providers.chat import OpenAIChatClient
from app.providers.llm_dialogue import LLMDialogueEngine
from app.providers.mock_dialogue import MockDialogueEngine
from app.providers.tts import MockSpeechSynthesizer, SpeechSynthesizer
from app.services.session_manager import SessionManager


@dataclass(frozen=True)
class Container:
    engine: DialogueEngine
    manager: SessionManager
    asr: SpeechRecognizer
    tts: SpeechSynthesizer


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

    return Container(
        engine=engine,
        manager=SessionManager(),
        asr=MockSpeechRecognizer(),
        tts=MockSpeechSynthesizer(),
    )


container = build_container(load_settings())
