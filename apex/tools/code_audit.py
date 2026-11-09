"""Automated Codebase Auditor & Security Posture Analyzer Tool for Apex."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


SECRET_PATTERNS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS Access Key ID", "🚨 HIGH"),
    (re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PGP|DSA)? ?PRIVATE KEY-----"), "Unencrypted Private Key", "🚨 CRITICAL"),
    (re.compile(r"""(?:api_key|apikey|secret_key|auth_token|client_secret)\s*[:=]\s*["']([A-Za-z0-9_\-\.]{16,})["']""", re.I), "Hardcoded API Secret Key", "🚨 HIGH"),
    (re.compile(r"""(?:password|passwd|db_pass)\s*[:=]\s*["']([^"'\s]{6,})["']""", re.I), "Hardcoded Password", "⚠️ MEDIUM"),
    (re.compile(r"\bghp_[a-zA-Z0-9]{36}\b"), "GitHub Personal Access Token", "🚨 HIGH"),
]

VULN_PATTERNS = [
    (re.compile(r"\b(?:eval|exec)\s*\("), "Dynamic Code Execution (eval/exec)", "⚠️ MEDIUM"),
    (re.compile(r"\bsubprocess\.(?:run|call|Popen)\s*\(.*shell\s*=\s*True", re.S), "Subprocess with shell=True Injection Risk", "⚠️ MEDIUM"),
    (re.compile(r"""(?:SELECT|INSERT|UPDATE|DELETE).*\+.*(?:request|input|param)""", re.I), "Potential Unsanitized SQL String Concatenation", "🚨 HIGH"),
    (re.compile(r"\bos\.system\s*\("), "Direct os.system invocation", "ℹ️ LOW"),
]


def audit_codebase(
    path: str = ".",
    scan_secrets: bool = True,
    scan_vulnerabilities: bool = True,
    max_files: int = 150
) -> str:
    """Run an automated security audit and code quality scan on a directory or file.

    Detects:
    - Hardcoded secrets, API tokens, AWS keys, and private certificates.
    - Code execution and injection vulnerabilities (eval, exec, shell=True).
    - Codebase volume, line counts, and file distribution.

    Args:
        path: Path to codebase directory or single file (default: '.').
        scan_secrets: Whether to scan for exposed credentials and tokens.
        scan_vulnerabilities: Whether to check for dangerous coding patterns.
        max_files: Maximum number of source files to inspect (default: 150).

    Returns:
        Structured Markdown audit report with severity ratings.
    """
    target = Path(os.path.expanduser(path))
    if not target.exists():
        return f"❌ Jalur tidak ditemukan: `{path}`"

    source_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".php", ".sh", ".env", ".json", ".yaml", ".yml"}
    files_to_scan: list[Path] = []

    if target.is_file():
        files_to_scan.append(target)
    else:
        for root, _, files in os.walk(target):
            if any(ign in root for ign in [".git", "__pycache__", ".venv", "node_modules", "dist", "build"]):
                continue
            for f in files:
                fp = Path(root) / f
                if fp.suffix.lower() in source_exts or fp.name.startswith(".env"):
                    files_to_scan.append(fp)
                    if len(files_to_scan) >= max_files:
                        break
            if len(files_to_scan) >= max_files:
                break

    findings: list[dict[str, Any]] = []
    total_lines = 0
    lang_counts: dict[str, int] = {}

    for fpath in files_to_scan:
        ext = fpath.suffix.lower() or fpath.name
        lang_counts[ext] = lang_counts.get(ext, 0) + 1

        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                total_lines += len(lines)

                for line_no, line in enumerate(lines, 1):
                    # Check Secrets
                    if scan_secrets:
                        for pat, title, severity in SECRET_PATTERNS:
                            if pat.search(line):
                                findings.append({
                                    "severity": severity,
                                    "type": title,
                                    "file": str(fpath.relative_to(target) if target.is_dir() else fpath.name),
                                    "line": line_no,
                                    "snippet": line.strip()[:100]
                                })

                    # Check Code Smells
                    if scan_vulnerabilities:
                        for pat, title, severity in VULN_PATTERNS:
                            if pat.search(line):
                                findings.append({
                                    "severity": severity,
                                    "type": title,
                                    "file": str(fpath.relative_to(target) if target.is_dir() else fpath.name),
                                    "line": line_no,
                                    "snippet": line.strip()[:100]
                                })

        except Exception:
            continue

    # Build Markdown Report
    status_icon = "🚨" if any("CRITICAL" in f["severity"] or "HIGH" in f["severity"] for f in findings) else ("⚠️" if findings else "✅")
    report = [
        f"🛡️ **Laporan Audit Kode & Postur Keamanan ({status_icon})** 🚀\n",
        f"• Target Audit: `{target.resolve()}`",
        f"• Berkas Diperiksa: **{len(files_to_scan)}** berkas ({total_lines:,} baris kode)",
        f"• Distribusi Bahasa: {', '.join(f'`{k}`: {v}' for k, v in list(lang_counts.items())[:5])}\n"
    ]

    if not findings:
        report.append("✅ **Status Bersih**: Tidak ditemukan kebocoran kredensial atau pola kerentanan berbahaya pada berkas yang dipindai!")
    else:
        report.append(f"### 📋 Temuan Temuan Keamanan ({len(findings)} Temuan):\n")
        # Sort by severity
        sorted_findings = sorted(findings, key=lambda x: ("CRITICAL" in x["severity"], "HIGH" in x["severity"], "MEDIUM" in x["severity"]), reverse=True)
        for idx, f in enumerate(sorted_findings[:15], 1):
            report.append(
                f"{idx}. {f['severity']} **{f['type']}**\n"
                f"   • Lokasi: `{f['file']}` (baris {f['line']})\n"
                f"   • Snippet: `{f['snippet']}`\n"
            )
        if len(sorted_findings) > 15:
            report.append(f"... *(+{len(sorted_findings) - 15} temuan lainnya)*\n")

    return "\n".join(report)
