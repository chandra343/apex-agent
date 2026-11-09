"""Unit tests for Learning & Lessons Store Tools."""
import pytest
from apex.tools.learning_ops import record_learned_lesson, consult_learned_lessons


def test_record_and_consult_lessons():
    rec_res = record_learned_lesson("git_push", "DONT", "Jangan push langsung ke branch main tanpa testing.")
    assert "Pelajaran Tersimpan" in rec_res
    assert "DONT" in rec_res

    consult_res = consult_learned_lessons("git_push")
    assert "Daftar Pelajaran" in consult_res
    assert "DONT" in consult_res
    assert "git_push" in consult_res


def test_record_lesson_invalid():
    res = record_learned_lesson("", "DO", "")
    assert "wajib diisi" in res
