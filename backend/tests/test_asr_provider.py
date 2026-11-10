"""Contract tests for the OpenAI-compatible ASR provider (G1, offline).

G1_OFFLINE: every real-provider behavior is pinned against a stubbed
httpx.post — request shape (multipart, auth, language hint), error
surface (HTTP status, timeout, empty transcript) and wiring rules
(explicit selection, no silent mock fallback, key required). No network,
no credentials.
"""

import base64

import httpx
import pytest

from app.core.config import Settings
from app.core.container import build_container
from app.providers.asr import OpenAIChatAudioTranscriber, OpenAICompatibleTranscriber

_TRANSCRIPTIONS_URL = "https://asr.test/v1/audio/transcriptions"
_CHAT_COMPLETIONS_URL = "https://asr.test/v1/chat/completions"


class _StubResponse:
    """Minimal httpx.Response stand-in for contract tests."""

    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {"text": "I like dogs."}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"error response {self.status_code}",
                request=httpx.Request("POST", _TRANSCRIPTIONS_URL),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


def _make_transcriber() -> OpenAICompatibleTranscriber:
    return OpenAICompatibleTranscriber(
        api_base="https://asr.test/v1",
        api_key="k-test",
        model="whisper-1",
    )


def test_transcribe_posts_multipart_with_auth_model_language(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url: str, **kwargs) -> _StubResponse:
        captured["url"] = url
        captured.update(kwargs)
        return _StubResponse(payload={"text": "  I like dogs.  "})

    monkeypatch.setattr("app.providers.asr.httpx.post", fake_post)
    text = _make_transcriber().transcribe(b"RIFF...", "audio/webm")

    assert text == "I like dogs."  # whitespace stripped
    assert captured["url"] == _TRANSCRIPTIONS_URL
    assert captured["headers"]["Authorization"] == "Bearer k-test"
    assert captured["data"]["model"] == "whisper-1"
    assert captured["data"]["language"] == "en"
    field_name = "file"  # dict key of the files mapping
    filename, content, content_type = captured["files"]["file"]
    assert field_name == "file"
    assert filename.endswith(".webm")
    assert content == b"RIFF..."
    assert content_type == "audio/webm"


@pytest.mark.parametrize(
    ("content_type", "expected_suffix"),
    [
        ("audio/wav", ".wav"),
        ("audio/x-wav", ".wav"),
        ("audio/mpeg", ".mp3"),
        ("audio/ogg", ".ogg"),
        ("audio/mp4", ".m4a"),
        ("audio/x-matroska", ".webm"),  # unknown -> webm kiosk default
    ],
)
def test_transcribe_maps_content_type_to_filename_suffix(
    monkeypatch, content_type: str, expected_suffix: str
) -> None:
    captured: dict = {}

    def fake_post(url: str, **kwargs) -> _StubResponse:
        captured.update(kwargs)
        return _StubResponse()

    monkeypatch.setattr("app.providers.asr.httpx.post", fake_post)
    _make_transcriber().transcribe(b"x", content_type)
    assert captured["files"]["file"][0].endswith(expected_suffix)


def test_transcribe_rejects_empty_transcript(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.providers.asr.httpx.post",
        lambda *a, **k: _StubResponse(payload={"text": "   "}),
    )
    with pytest.raises(RuntimeError):
        _make_transcriber().transcribe(b"x", "audio/webm")


def test_transcribe_surfaces_http_status_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.providers.asr.httpx.post",
        lambda *a, **k: _StubResponse(status_code=429),  # quota exceeded
    )
    with pytest.raises(httpx.HTTPStatusError):
        _make_transcriber().transcribe(b"x", "audio/webm")


def test_transcribe_surfaces_timeouts(monkeypatch) -> None:
    def fake_post(*a, **k) -> None:
        raise httpx.ConnectTimeout(
            "timed out", request=httpx.Request("POST", _TRANSCRIPTIONS_URL)
        )

    monkeypatch.setattr("app.providers.asr.httpx.post", fake_post)
    with pytest.raises(httpx.TimeoutException):
        _make_transcriber().transcribe(b"x", "audio/webm")


def test_container_requires_key_for_openai_asr() -> None:
    with pytest.raises(ValueError, match="ASR_API_KEY"):
        build_container(Settings(asr_provider="openai"))


def test_container_selects_openai_transcriber() -> None:
    container = build_container(Settings(asr_provider="openai", asr_api_key="k-test"))
    assert isinstance(container.asr, OpenAICompatibleTranscriber)


def test_container_rejects_unknown_asr_provider() -> None:
    with pytest.raises(ValueError, match="ASR_PROVIDER"):
        build_container(Settings(asr_provider="azure"))


class _StubChatResponse(_StubResponse):
    """Stub whose default payload mirrors a chat-completions reply."""

    def __init__(self, status_code: int = 200, content: str = "I like dogs.") -> None:
        super().__init__(
            status_code=status_code,
            payload={"choices": [{"message": {"content": content}}]},
        )

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"error response {self.status_code}",
                request=httpx.Request("POST", _CHAT_COMPLETIONS_URL),
                response=httpx.Response(self.status_code),
            )


def _make_chat_transcriber() -> OpenAIChatAudioTranscriber:
    return OpenAIChatAudioTranscriber(
        api_base="https://asr.test/v1",
        api_key="k-test",
        model="qwen3-omni-flash",
    )


def test_chat_transcriber_posts_data_uri_audio_and_extracts_content(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url: str, **kwargs) -> _StubChatResponse:
        captured["url"] = url
        captured.update(kwargs)
        return _StubChatResponse(content="  I like cats. \n")

    monkeypatch.setattr("app.providers.asr.httpx.post", fake_post)
    text = _make_chat_transcriber().transcribe(b"RIFF...", "audio/wav")

    assert text == "I like cats."  # whitespace stripped
    assert captured["url"] == _CHAT_COMPLETIONS_URL
    assert captured["headers"]["Authorization"] == "Bearer k-test"
    assert captured["timeout"] == 10.0
    body = captured["json"]
    assert body["model"] == "qwen3-omni-flash"
    assert body["modalities"] == ["text"]  # transcript only, no speech out
    audio_part, instruction_part = body["messages"][0]["content"]
    assert audio_part["type"] == "input_audio"
    assert audio_part["input_audio"]["format"] == "wav"
    assert audio_part["input_audio"]["data"] == (
        "data:audio/wav;base64," + base64.b64encode(b"RIFF...").decode("ascii")
    )
    assert "Transcribe" in instruction_part["text"]


@pytest.mark.parametrize(
    ("content_type", "expected_format"),
    [
        ("audio/wav", "wav"),
        ("audio/x-wav", "wav"),
        ("audio/mpeg", "mp3"),
        ("audio/ogg", "ogg"),
        ("audio/mp4", "m4a"),
        ("audio/webm;codecs=opus", "webm"),
        ("audio/x-matroska", "webm"),  # unknown -> kiosk default container
    ],
)
def test_chat_transcriber_maps_content_type_to_audio_format(
    monkeypatch, content_type: str, expected_format: str
) -> None:
    captured: dict = {}

    def fake_post(url: str, **kwargs) -> _StubChatResponse:
        captured.update(kwargs)
        return _StubChatResponse()

    monkeypatch.setattr("app.providers.asr.httpx.post", fake_post)
    _make_chat_transcriber().transcribe(b"x", content_type)
    assert captured["json"]["messages"][0]["content"][0]["input_audio"][
        "format"
    ] == expected_format


def test_chat_transcriber_rejects_empty_content(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.providers.asr.httpx.post",
        lambda *a, **k: _StubChatResponse(content="   "),
    )
    with pytest.raises(RuntimeError):
        _make_chat_transcriber().transcribe(b"x", "audio/webm")


def test_chat_transcriber_surfaces_http_status_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.providers.asr.httpx.post",
        lambda *a, **k: _StubChatResponse(status_code=429),
    )
    with pytest.raises(httpx.HTTPStatusError):
        _make_chat_transcriber().transcribe(b"x", "audio/webm")


def test_container_requires_key_for_openai_chat_asr() -> None:
    with pytest.raises(ValueError, match="ASR_API_KEY"):
        build_container(Settings(asr_provider="openai-chat"))


def test_container_selects_chat_audio_transcriber() -> None:
    container = build_container(
        Settings(asr_provider="openai-chat", asr_api_key="k-test")
    )
    assert isinstance(container.asr, OpenAIChatAudioTranscriber)
