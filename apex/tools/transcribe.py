"""Audio Voice Transcription Tool (Whisper STT Integration)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple
import requests
from apex.config import config


def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    prompt: Optional[str] = None
) -> Tuple[bool, str]:
    """Transcribe an audio file (e.g. voice note from Telegram/WhatsApp) to text.

    Supports: ogg, opus, mp3, m4a, wav, webm, flac.
    """
    p = Path(audio_path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return False, f"Audio file not found: {p}"

    # Determine STT endpoint (prefer Groq Whisper if available, or OpenAI)
    providers = config.get("providers", {})
    api_key = ""
    base_url = ""
    model = "whisper-large-v3"

    if "groq" in providers and providers["groq"].get("api_key"):
        api_key = providers["groq"]["api_key"]
        base_url = providers["groq"].get("base_url", "https://api.groq.com/openai/v1").rstrip("/")
        model = "whisper-large-v3"
    elif "openai" in providers and providers["openai"].get("api_key"):
        api_key = providers["openai"]["api_key"]
        base_url = providers["openai"].get("base_url", "https://api.openai.com/v1").rstrip("/")
        model = "whisper-1"
    else:
        # Check environment
        api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        base_url = "https://api.groq.com/openai/v1" if os.environ.get("GROQ_API_KEY") else "https://api.openai.com/v1"

    if not api_key or "YOUR_" in api_key:
        return False, "No active API key configured for audio transcription (Groq or OpenAI required)."

    url = f"{base_url}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}

    data = {"model": model}
    if language:
        data["language"] = language
    if prompt:
        data["prompt"] = prompt

    try:
        with open(p, "rb") as audio_file:
            files = {"file": (p.name, audio_file, "audio/mpeg")}
            resp = requests.post(url, headers=headers, data=data, files=files, timeout=60)

        if resp.status_code == 200:
            result = resp.json()
            text = result.get("text", "").strip()
            return True, text
        else:
            return False, f"Transcription API failed (HTTP {resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return False, f"Audio transcription error: {e}"
