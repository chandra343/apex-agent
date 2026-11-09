"""Unit tests for Codebase Auditor & Security Posture Analyzer."""
import pytest
from apex.tools.code_audit import audit_codebase


def test_audit_codebase_detects_secrets(tmp_path):
    vuln_file = tmp_path / "insecure_script.py"
    vuln_file.write_text("""
def run_app():
    api_key = "AKIA1234567890ABCDEF"
    eval("print('hello')")
""")

    report = audit_codebase(path=str(vuln_file))
    assert "Laporan Audit Kode" in report
    assert "AWS Access Key ID" in report
    assert "eval" in report or "Dynamic Code Execution" in report


def test_audit_codebase_clean(tmp_path):
    clean_file = tmp_path / "clean_math.py"
    clean_file.write_text("""
def add(a, b):
    return a + b
""")

    report = audit_codebase(path=str(clean_file))
    assert "Status Bersih" in report
