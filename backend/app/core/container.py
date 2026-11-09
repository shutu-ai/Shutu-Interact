"""Process-wide singletons wiring providers into the API routes.

REPLACEMENT POINT: swap Mock* instances for cloud providers here — routes
depend only on the protocols.
"""

from dataclasses import dataclass

from app.providers.asr import MockSpeechRecognizer, SpeechRecognizer
from app.providers.base import DialogueEngine
from app.providers.mock_dialogue import MockDialogueEngine
from app.providers.tts import MockSpeechSynthesizer, SpeechSynthesizer
from app.services.session_manager import SessionManager


@dataclass(frozen=True)
class Container:
    engine: DialogueEngine
    manager: SessionManager
    asr: SpeechRecognizer
    tts: SpeechSynthesizer


container = Container(
    engine=MockDialogueEngine(),
    manager=SessionManager(),
    asr=MockSpeechRecognizer(),
    tts=MockSpeechSynthesizer(),
)
