"""Speech recognition provider protocol and implementations.

Selection happens in app/core/container.py via ASR_PROVIDER:
- "mock"  : deterministic scripted transcript (offline demo/dev only)
- "openai": OpenAI-compatible /audio/transcriptions endpoint (real)

The mock is never a silent fallback: selecting a real provider without
credentials fails fast at startup (container build).
"""

import httpx
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


_TIMEOUT_SECONDS = 10.0

_CONTENT_TYPE_EXTENSIONS: dict[str, str] = {
    "audio/webm": ".webm",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
}


class OpenAICompatibleTranscriber:
    """POST {api_base}/audio/transcriptions (OpenAI wire format).

    Works with any endpoint exposing that schema (OpenAI, Azure-compatible
    gateways, domestic providers). The API key lives only in server env
    (ASR_API_KEY) and is never sent to the browser. Speech audio goes
    straight from request body to provider; nothing is logged or stored.
    """

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        timeout_seconds: float = _TIMEOUT_SECONDS,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def _filename_for(self, content_type: str) -> str:
        base_type = content_type.split(";")[0].strip().lower()
        extension = _CONTENT_TYPE_EXTENSIONS.get(base_type, ".webm")
        return f"speech{extension}"

    def transcribe(self, audio: bytes, content_type: str) -> str:
        response = httpx.post(
            f"{self._api_base}/audio/transcriptions",
            files={"file": (self._filename_for(content_type), audio, content_type)},
            data={"model": self._model, "language": "en"},
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        text = response.json().get("text", "")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Empty transcription from ASR provider")
        return text.strip()


class MockSpeechRecognizer:
    """Deterministic mock: always 'hears' the same sentence.

    Keeps the full voice loop exercisable without cloud credentials.
    """

    _TRANSCRIPT = "I like dogs."

    def transcribe(self, audio: bytes, content_type: str) -> str:
        if not audio:
            return ""
        return self._TRANSCRIPT
