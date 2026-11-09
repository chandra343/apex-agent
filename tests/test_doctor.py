"""Unit tests for System Doctor & Self-Healing Tool."""
import pytest
from apex.tools.doctor import run_system_doctor


def test_run_system_doctor():
    report = run_system_doctor(auto_repair=True)
    assert "Kartu Diagnostik Kesehatan Sistem Apex" in report
    assert "Struktur Direktori" in report
    assert "Integritas Basis Data SQLite" in report
    assert "Status Provider AI" in report
