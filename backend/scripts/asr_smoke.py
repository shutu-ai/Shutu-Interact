r"""Manual live smoke test for the real ASR provider (G1_LIVE).

Sends one local audio file to the configured OpenAI-compatible endpoint
and prints the transcript. Credentials come from the environment only —
never hardcode or commit keys.

Usage (from backend/, with the venv active):
    set ASR_PROVIDER=openai
    set ASR_API_BASE=https://api.openai.com/v1
    set ASR_API_KEY=sk-...            (shell session only; do not save)
    set ASR_MODEL=whisper-1
    .venv/Scripts/python.exe scripts/asr_smoke.py path\to\sample.wav

Authorized audio only: an adult speaking a short English sentence
(e.g. "I like cats."). Never use a child's voice or any personal data.
"""

import os
import sys

import httpx


def main() -> int:
    api_base = os.getenv("ASR_API_BASE", "").strip()
    api_key = os.getenv("ASR_API_KEY", "").strip()
    model = os.getenv("ASR_MODEL", "whisper-1").strip() or "whisper-1"

    if not api_base or not api_key:
        print("ERROR: set ASR_API_BASE and ASR_API_KEY in the environment first.")
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
    print(f"POST {api_base.rstrip('/')}/audio/transcriptions (model={model})")
    try:
        response = httpx.post(
            f"{api_base.rstrip('/')}/audio/transcriptions",
            files={"file": (filename, audio)},
            data={"model": model, "language": "en"},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"ERROR: request failed: {type(exc).__name__}: {exc}")
        return 1

    transcript = response.json().get("text", "")
    print(f"TRANSCRIPT: {transcript!r}")
    if not transcript.strip():
        print("WARNING: provider returned an empty transcript.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
