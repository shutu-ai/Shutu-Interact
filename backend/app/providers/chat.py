"""Chat completion client protocol and OpenAI-compatible implementation.

REPLACEMENT POINT: any OpenAI-compatible endpoint works (Azure OpenAI,
DeepSeek, Qwen, local vLLM...). Configure via LLM_API_BASE / LLM_API_KEY /
LLM_MODEL in the environment.
"""

import httpx
from typing import Protocol

_TIMEOUT_SECONDS = 6.0
_MAX_TOKENS = 80


class ChatClient(Protocol):
    """Minimal chat-completions surface the dialogue engine needs."""

    def complete(self, system_prompt: str, history: list[dict[str, str]]) -> str:
        """Return the assistant text for one completion call."""
        ...


class OpenAIChatClient:
    """Thin adapter for POST {api_base}/chat/completions."""

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        timeout_seconds: float = _TIMEOUT_SECONDS,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._timeout_seconds = timeout_seconds

    def complete(self, system_prompt: str, history: list[dict[str, str]]) -> str:
        payload = {
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": _MAX_TOKENS,
            "messages": [
                {"role": "system", "content": system_prompt},
                *history,
            ],
        }
        response = httpx.post(
            f"{self._api_base}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Empty chat completion")
        return content.strip()
