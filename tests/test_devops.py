"""Unit tests for DevOps & CI/CD Test Runner Tools."""
import pytest
from apex.tools.devops import run_project_tests, create_git_patch


def test_run_project_tests_self():
    # Target a single fast test file to prevent recursive pytest execution
    res = run_project_tests(path=".", framework="pytest tests/test_doctor.py -q")
    assert "Laporan Hasil Pengujian Proyek" in res
    assert "Perintah" in res


def test_run_project_tests_invalid_path():
    res = run_project_tests(path="/non_existent_folder_abc_123")
    assert "tidak ditemukan" in res


def test_create_git_patch():
    res = create_git_patch()
    assert ("Operasi Git DevOps" in res) or ("Tidak ada perubahan file" in res)
