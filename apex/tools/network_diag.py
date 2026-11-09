"""Network, SSL/TLS, and API Diagnostic Suite for Project Apex."""
from __future__ import annotations

import datetime
import socket
import ssl
import time
from typing import Any, Dict, List, Optional
import requests


def benchmark_http_endpoint(
    url: str,
    request_count: int = 5
) -> str:
    """Benchmark an HTTP/HTTPS endpoint measuring latency percentiles, TTFB, and status codes.

    Args:
        url: Target web or API URL (e.g. 'https://api.github.com' or 'http://localhost:8000').
        request_count: Number of benchmark probe requests to send (default: 5, max: 20).

    Returns:
        Structured benchmark report with min, max, average latencies, and status distribution.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    count = max(1, min(request_count, 20))
    latencies: list[float] = []
    status_codes: dict[int, int] = {}

    headers = {"User-Agent": "Apex-Network-Diagnostic/1.0"}

    for _ in range(count):
        start_t = time.time()
        try:
            resp = requests.get(clean_url, headers=headers, timeout=10)
            lat = round((time.time() - start_t) * 1000, 2)
            latencies.append(lat)
            status_codes[resp.status_code] = status_codes.get(resp.status_code, 0) + 1
        except Exception as e:
            latencies.append(-1.0)
            status_codes[0] = status_codes.get(0, 0) + 1

    valid_lats = [l for l in latencies if l >= 0]
    if not valid_lats:
        return f"❌ Gagal melakukan benchmark pada `{clean_url}`. Semua permintaan timeout atau error."

    avg_lat = round(sum(valid_lats) / len(valid_lats), 2)
    min_lat = min(valid_lats)
    max_lat = max(valid_lats)

    status_str = ", ".join(f"HTTP {code}: {cnt}x" if code != 0 else f"Failed: {cnt}x" for code, cnt in status_codes.items())

    return (
        f"⚡ **Hasil Benchmark HTTP Endpoint** 🚀\n\n"
        f"• Target URL: `{clean_url}`\n"
        f"• Total Permintaan: **{count}** probe\n"
        f"• Latensi Rata-rata: **{avg_lat} ms**\n"
        f"• Latensi Tercepat / Terlama: **{min_lat} ms** / **{max_lat} ms**\n"
        f"• Distribusi Status: `{status_str}`"
    )


def check_ssl_certificate(host: str, port: int = 443) -> str:
    """Inspect SSL/TLS certificate validity, expiry date, days remaining, and issuer.

    Args:
        host: Hostname or domain name (e.g. 'google.com', 'github.com').
        port: TLS port (default: 443).

    Returns:
        Structured certificate security health report.
    """
    clean_host = host.strip().replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]

    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((clean_host, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=clean_host) as ssock:
                cert = ssock.getpeercert()
                tls_version = ssock.version()
                cipher = ssock.cipher()

        if not cert:
            return f"⚠️ Tidak dapat membaca sertifikat SSL dari `{clean_host}`."

        # Parse expiry date
        not_after_str = cert.get("notAfter", "")
        # Format: 'May 15 12:00:00 2026 GMT'
        expiry_dt = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
        now_dt = datetime.datetime.utcnow()
        days_left = (expiry_dt - now_dt).days

        # Issuer
        issuer_dict = dict(x[0] for x in cert.get("issuer", ()))
        issuer_name = issuer_dict.get("organizationName") or issuer_dict.get("commonName") or "Unknown Issuer"

        # Subject
        subj_dict = dict(x[0] for x in cert.get("subject", ()))
        common_name = subj_dict.get("commonName", clean_host)

        status_badge = "✅ AKTIF SEHAT" if days_left > 14 else ("⚠️ AKAN KADALUWARSA" if days_left > 0 else "🚨 KADALUWARSA")

        return (
            f"🔒 **Laporan Diagnostik Sertifikat SSL/TLS ({status_badge})** 🛡️\n\n"
            f"• Host: `{clean_host}:{port}`\n"
            f"• Common Name (CN): `{common_name}`\n"
            f"• Penerbit (Issuer): **{issuer_name}**\n"
            f"• Protokol: `{tls_version}` ({cipher[0] if cipher else 'Standard'})\n"
            f"• Tanggal Kadaluwarsa: **{expiry_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}**\n"
            f"• Sisa Masa Berlaku: **{days_left} hari lagi**"
        )

    except Exception as e:
        return f"❌ Gagal memeriksa sertifikat SSL pada `{clean_host}`: {str(e)}"


def lookup_dns_records(domain: str, record_type: str = "A") -> str:
    """Resolve DNS address records for a domain using native socket resolution.

    Args:
        domain: Target domain name (e.g. 'github.com', 'cloudflare.com').
        record_type: 'A' (IPv4) or 'AAAA' (IPv6).

    Returns:
        Structured DNS resolution results.
    """
    clean_domain = domain.strip().replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]

    try:
        family = socket.AF_INET6 if record_type.upper() == "AAAA" else socket.AF_INET
        results = socket.getaddrinfo(clean_domain, None, family=family)
        ips = list(set(r[4][0] for r in results))

        if not ips:
            return f"⚠️ Tidak ditemukan record DNS `{record_type.upper()}` untuk domain `{clean_domain}`."

        ip_list = "\n".join(f"• `{ip}`" for ip in ips)
        return (
            f"🌐 **Hasil Resolusi DNS ({record_type.upper()})**:\n\n"
            f"• Domain: `{clean_domain}`\n"
            f"• IP Addresses Ditemukan:\n{ip_list}"
        )
    except Exception as e:
        return f"❌ Gagal melakukan DNS lookup untuk `{clean_domain}`: {str(e)}"
