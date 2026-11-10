"""Speech recognition provider protocol and implementations.

Selection happens in app/core/container.py via ASR_PROVIDER:
- "mock"       : deterministic scripted transcript (offline demo/dev only)
- "openai"     : OpenAI-compatible /audio/transcriptions endpoint (real)
- "openai-chat": OpenAI-compatible /chat/completions with base64
                 input_audio, for gateways that expose audio through the
                 chat wire format (e.g. Alibaba Bailian compatible-mode
                 with qwen-omni chat models) instead of the
                 transcriptions endpoint (real)

The mock is never a silent fallback: selecting a real provider without
credentials fails fast at startup (container build).
"""

import base64

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


class OpenAIChatAudioTranscriber:
    """POST {api_base}/chat/completions with a base64 input_audio part.

    For OpenAI-compatible gateways that expose speech input through the
    chat wire format (model must be an audio-capable chat model such as
    qwen3-omni-flash). The audio travels as a data: URI, so no public
    file host is needed; the reply content is the transcript. Credentials
    live only in server env and the audio is never logged or stored.
    """

    _INSTRUCTION = (
        "Transcribe the audio. Output only the exact English words spoken."
    )

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

    def _format_for(self, content_type: str) -> str:
        base_type = content_type.split(";")[0].strip().lower()
        return _CONTENT_TYPE_EXTENSIONS.get(base_type, ".webm").lstrip(".")

    def transcribe(self, audio: bytes, content_type: str) -> str:
        encoded = base64.b64encode(audio).decode("ascii")
        response = httpx.post(
            f"{self._api_base}/chat/completions",
            json={
                "model": self._model,
                "modalities": ["text"],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": f"data:{content_type};base64,{encoded}",
                                    "format": self._format_for(content_type),
                                },
                            },
                            {"type": "text", "text": self._INSTRUCTION},
                        ],
                    }
                ],
            },
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        choice = response.json()["choices"][0]
        content = choice["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Empty transcription from ASR provider")
        return content.strip()


class MockSpeechRecognizer:
    """Deterministic mock: always 'hears' the same sentence.

    Keeps the full voice loop exercisable without cloud credentials.
    """

    _TRANSCRIPT = "I like dogs."

    def transcribe(self, audio: bytes, content_type: str) -> str:
        if not audio:
            return ""
        return self._TRANSCRIPT
