"""Text-to-Speech (TTS) Audio Synthesis Tool for Apex."""
from __future__ import annotations

import os
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional
import requests

from apex.config import DATA_DIR


def synthesize_speech(
    text: str,
    output_path: Optional[str] = None,
    language: str = "id"
) -> str:
    """Synthesize text into an audio file (MP3/WAV) using resilient zero-cost TTS engines.

    Args:
        text: Text to synthesize into speech.
        output_path: Optional destination audio file path. Defaults to ~/.apex/audio/tts_<timestamp>.mp3.
        language: Language code for speech synthesis (default: 'id' for Indonesian, 'en' for English).

    Returns:
        Confirmation string with audio file path and byte size.
    """
    clean_text = text.strip()
    if not clean_text:
        return "❌ Teks kosong. Berikan teks yang ingin diubah menjadi suara."

    audio_dir = DATA_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    if not output_path:
        import time
        output_file = audio_dir / f"speech_{int(time.time())}.mp3"
    else:
        output_file = Path(os.path.expanduser(output_path))
        output_file.parent.mkdir(parents=True, exist_ok=True)

    # Strategy 1: Google TTS Endpoint (High quality natural audio)
    try:
        # Split text into chunks <= 150 chars for the endpoint
        chunks = []
        words = clean_text.split()
        curr_chunk: list[str] = []
        curr_len = 0

        for w in words:
            if curr_len + len(w) + 1 > 150:
                chunks.append(" ".join(curr_chunk))
                curr_chunk = [w]
                curr_len = len(w)
            else:
                curr_chunk.append(w)
                curr_len += len(w) + 1
        if curr_chunk:
            chunks.append(" ".join(curr_chunk))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        with open(output_file, "wb") as f_out:
            for c in chunks[:10]:  # Limit to first 10 chunks to avoid excessive downloads
                encoded_q = urllib.parse.quote(c)
                url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_q}&tl={language}&client=tw-ob"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    f_out.write(resp.content)

        if output_file.exists() and output_file.stat().st_size > 0:
            sz_kb = round(output_file.stat().st_size / 1024, 2)
            return f"🎙️ **Audio TTS Berhasil Dibuat**: `{output_file}` ({sz_kb} KB, bahasa: `{language}`) 🔊"

    except Exception:
        pass

    # Strategy 2: Local espeak-ng / espeak fallback (if installed on host Linux)
    espeak_bin = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak_bin:
        try:
            wav_file = output_file.with_suffix(".wav")
            subprocess.run([espeak_bin, "-v", language, "-w", str(wav_file), clean_text[:500]], check=True)
            if wav_file.exists() and wav_file.stat().st_size > 0:
                sz_kb = round(wav_file.stat().st_size / 1024, 2)
                return f"🎙️ **Audio TTS Berhasil Dibuat (Lokal espeak)**: `{wav_file}` ({sz_kb} KB) 🔊"
        except Exception:
            pass

    return f"⚠️ Gagal mensintesis audio. Periksa koneksi internet atau instalasi 'espeak-ng'."
