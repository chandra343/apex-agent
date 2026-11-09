"""Unit tests for Network & SSL Diagnostic Tools."""
import pytest
from apex.tools.network_diag import benchmark_http_endpoint, check_ssl_certificate, lookup_dns_records


def test_lookup_dns_records():
    res = lookup_dns_records("localhost", record_type="A")
    assert "Hasil Resolusi DNS" in res
    assert "127.0.0.1" in res or "localhost" in res


def test_check_ssl_certificate_invalid():
    res = check_ssl_certificate("localhost_non_ssl_test", port=9999)
    assert "Gagal" in res or "tidak dapat" in res.lower()
