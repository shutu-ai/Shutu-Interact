"""Speech recognition provider protocol and mock implementation.

REPLACEMENT POINT: implement SpeechRecognizer with a cloud ASR (Azure /
Google / iFlytek) and swap the instance in app/core/container.py.
"""

from typing import Protocol


class SpeechRecognizer(Protocol):
    def transcribe(self, audio: bytes, content_type: str) -> str:
        """Return the English transcript for a recorded utterance."""
        ...


class MockSpeechRecognizer:
    """Deterministic mock: always 'hears' the same sentence.

    Keeps the full voice loop exercisable without cloud credentials.
    """

    _TRANSCRIPT = "I like dogs."

    def transcribe(self, audio: bytes, content_type: str) -> str:
        if not audio:
            return ""
        return self._TRANSCRIPT
