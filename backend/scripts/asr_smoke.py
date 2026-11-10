r"""Manual live smoke test for the real ASR provider (G1_LIVE).

Sends one local audio file to the configured real ASR provider and
prints the transcript. Credentials come from the environment only —
never hardcode or commit keys.

Usage (from backend/, with the venv active):
    set ASR_PROVIDER=openai            (or openai-chat)
    set ASR_API_BASE=https://api.openai.com/v1
    set ASR_API_KEY=sk-...            (shell session only; do not save)
    set ASR_MODEL=whisper-1            (or an audio chat model, e.g. qwen3-omni-flash)
    .venv/Scripts/python.exe scripts/asr_smoke.py path\to\sample.wav

Authorized audio only: an adult speaking a short English sentence
(e.g. "I like cats."). Never use a child's voice or any personal data.
"""

import base64
import os
import sys

import httpx


def _transcribe_transcriptions(
    api_base: str, api_key: str, model: str, audio: bytes, filename: str
) -> str:
    response = httpx.post(
        f"{api_base.rstrip('/')}/audio/transcriptions",
        files={"file": (filename, audio)},
        data={"model": model, "language": "en"},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json().get("text", "")


def _transcribe_chat_audio(
    api_base: str, api_key: str, model: str, audio: bytes, filename: str
) -> str:
    extension = os.path.splitext(filename)[1].lstrip(".") or "webm"
    encoded = base64.b64encode(audio).decode("ascii")
    response = httpx.post(
        f"{api_base.rstrip('/')}/chat/completions",
        json={
            "model": model,
            "modalities": ["text"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:audio/{extension};base64,{encoded}",
                                "format": extension,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Transcribe the audio. Output only the "
                            "exact English words spoken.",
                        },
                    ],
                }
            ],
        },
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60.0,
    )
    response.raise_for_status()
    choice = response.json()["choices"][0]
    content = choice["message"]["content"]
    return content if isinstance(content, str) else ""


def main() -> int:
    api_base = os.getenv("ASR_API_BASE", "").strip()
    api_key = os.getenv("ASR_API_KEY", "").strip()
    provider = os.getenv("ASR_PROVIDER", "openai").strip()
    model = os.getenv("ASR_MODEL", "whisper-1").strip() or "whisper-1"

    if not api_base or not api_key:
        print("ERROR: set ASR_API_BASE and ASR_API_KEY in the environment first.")
        return 2
    if provider not in ("openai", "openai-chat"):
        print(f"ERROR: ASR_PROVIDER must be 'openai' or 'openai-chat', got {provider!r}.")
        return 2
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    audio_path = sys.argv[1]
    try:
        with open(audio_path, "rb") as f:
            audio = f.read()
    except OSError as exc:
        print(f"ERROR: cannot read {audio_path}: {exc}")
        return 2
    if not audio:
        print(f"ERROR: {audio_path} is empty.")
        return 2

    filename = os.path.basename(audio_path)
    endpoint = (
        "audio/transcriptions" if provider == "openai" else "chat/completions"
    )
    print(f"POST {api_base.rstrip('/')}/{endpoint} (model={model})")
    try:
        if provider == "openai":
            transcript = _transcribe_transcriptions(
                api_base, api_key, model, audio, filename
            )
        else:
            transcript = _transcribe_chat_audio(
                api_base, api_key, model, audio, filename
            )
    except httpx.HTTPError as exc:
        print(f"ERROR: request failed: {type(exc).__name__}: {exc}")
        return 1

    print(f"TRANSCRIPT: {transcript!r}")
    if not transcript.strip():
        print("WARNING: provider returned an empty transcript.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
