"""Speech synthesis provider protocol and mock implementation.

REPLACEMENT POINT: implement SpeechSynthesizer with a cloud TTS and swap
the instance in app/core/container.py. The MVP frontend speaks via
browser speechSynthesis by default; this endpoint exists so a cloud
provider can be adopted without any route change.
"""

import io
import wave
from typing import Protocol

_SAMPLE_RATE = 16000
_DURATION_SECONDS = 0.5


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str) -> bytes:
        """Return WAV audio bytes speaking the given text."""
        ...


class MockSpeechSynthesizer:
    """Generates a short silent WAV — valid audio without a cloud call."""

    def synthesize(self, text: str) -> bytes:
        frame_count = int(_SAMPLE_RATE * _DURATION_SECONDS)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(_SAMPLE_RATE)
            wav.writeframes(b"\x00\x00" * frame_count)
        return buffer.getvalue()
