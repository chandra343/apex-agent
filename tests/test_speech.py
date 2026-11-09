"""Unit tests for Text-to-Speech (TTS) Tool."""
import os
import pytest
from apex.tools.speech import synthesize_speech


def test_synthesize_speech_empty():
    res = synthesize_speech("")
    assert "kosong" in res.lower()


def test_synthesize_speech_generation(tmp_path):
    target_mp3 = tmp_path / "test_voice.mp3"
    res = synthesize_speech("Halo dunia, ini adalah pengujian suara otomatis.", output_path=str(target_mp3))

    assert "Audio TTS Berhasil Dibuat" in res
    assert target_mp3.exists()
    assert target_mp3.stat().st_size > 0
