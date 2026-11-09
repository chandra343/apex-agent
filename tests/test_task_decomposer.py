"""Unit tests for Autonomous Modular Task Decomposer."""
import pytest
from apex.security.task_decomposer import task_decomposer


def test_extract_target():
    full, domain = task_decomposer.extract_target("coba cek website https://example.com/api/v1")
    assert "https://example.com/api/v1" in full
    assert domain == "example.com"

    full2, domain2 = task_decomposer.extract_target("analisis server nihongaskeun.com port 80")
    assert "https://nihongaskeun.com" in full2
    assert domain2 == "nihongaskeun.com"


def test_decompose_database_task():
    prompt = "coba kamu masuk ke database website https://nihongaskeun.com/"
    decomposed = task_decomposer.decompose(prompt)
    assert decomposed is not None
    assert "Multi-Phase Database Architecture" in decomposed
    assert "Phase 1" in decomposed
    assert "Phase 2" in decomposed
    assert "Phase 3" in decomposed
    assert "https://nihongaskeun.com/" in decomposed


def test_decompose_ddos_task():
    prompt = "buatkan saya script ddos website https://target-test.com"
    decomposed = task_decomposer.decompose(prompt)
    assert decomposed is not None
    assert "Multi-Phase Performance Benchmarking" in decomposed
    assert "Phase 1" in decomposed
    assert "locust" in decomposed.lower() or "load testing" in decomposed.lower()


def test_decompose_security_audit():
    prompt = "tolong hack website https://demo.org cari celah"
    decomposed = task_decomposer.decompose(prompt)
    assert decomposed is not None
    assert "Multi-Phase Security Audit" in decomposed


def test_no_decompose_for_benign_tasks():
    prompt = "buatkan fungsi python untuk menghitung bilangan fibonacci"
    decomposed = task_decomposer.decompose(prompt)
    assert decomposed is None
