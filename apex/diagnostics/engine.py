"""Autonomous Tool Self-Healing & Stderr Diagnostics Engine (OpenBot & Hermes Style)."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# Regex for ANSI terminal escape sequences
ANSI_REGEX = re.compile(
    r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\].*?(?:\x07|\x1B\\))"
)

# Common credential patterns to redact
SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "sk-[REDACTED_API_KEY]"),
    (re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE), "ghp_[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"ey[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "[REDACTED_JWT_TOKEN]"),
    (re.compile(r"(password|passwd|secret|api_key|apikey|token)\s*[:=]\s*['\"]?([^\s'\"]{6,})['\"]?", re.IGNORECASE), r"\1=***REDACTED***"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE), "Bearer [REDACTED_AUTH_TOKEN]"),
]


class DiagnosticRule:
    def __init__(self, pattern: str, title: str, hint_template: str, flags: int = re.IGNORECASE):
        self.regex = re.compile(pattern, flags)
        self.title = title
        self.hint_template = hint_template

    def match(self, text: str) -> Optional[str]:
        m = self.regex.search(text)
        if m:
            try:
                return self.hint_template.format(*m.groups())
            except Exception:
                return self.hint_template
        return None


RULES: List[DiagnosticRule] = [
    DiagnosticRule(
        r"ModuleNotFoundError:\s+No module named ['\"]([^'\"]+)['\"]",
        "Python Module Missing",
        "Modul Python '{0}' belum terpasang. Jalankan `.venv/bin/pip install {0}` atau periksa virtual environment."
    ),
    DiagnosticRule(
        r"ImportError:\s+cannot import name ['\"]([^'\"]+)['\"]",
        "Import Error",
        "Gagal mengimpor '{0}'. Kemungkinan terjadi circular import atau versi package tidak cocok."
    ),
    DiagnosticRule(
        r"(?:bash|sh):\s*(?:line \d+:\s*)?([^:]+):\s*command not found",
        "Command Not Found",
        "Perintah '{0}' tidak ditemukan di PATH sistem. Periksa instalasi binary atau gunakan path absolut."
    ),
    DiagnosticRule(
        r"FileNotFoundError:\s*\[Errno 2\]\s*No such file or directory:\s*['\"]?([^'\"\n]+)['\"]?",
        "File/Path Not Found",
        "File atau direktori '{0}' tidak ditemukan. Periksa typo pada path atau buat direktori terlebih dahulu."
    ),
    DiagnosticRule(
        r"PermissionError:\s*\[Errno 13\]\s*Permission denied:\s*['\"]?([^'\"\n]+)['\"]?",
        "Permission Denied",
        "Izin akses ditolak ke '{0}'. Periksa hak akses file (chmod/chown) atau jalankan dengan izin yang memadai."
    ),
    DiagnosticRule(
        r"(?:Address already in use|\[Errno 98\] Address already in use|bind: address already in use)",
        "Port Conflict",
        "Port jaringan yang diminta sedang dipakai oleh proses lain. Jalankan `lsof -i :<port>` atau ganti port alternatif."
    ),
    DiagnosticRule(
        r"(?:ConnectionRefusedError:\s*\[Errno 111\] Connection refused|Failed to connect to (?:localhost|127\.0\.0\.1|0\.0\.0\.0))",
        "Connection Refused",
        "Layanan target tidak sedang berjalan atau tidak mendengarkan port yang dituju. Pastikan daemon/server sudah start."
    ),
    DiagnosticRule(
        r"sqlite3\.OperationalError:\s*database is locked",
        "Database Locked",
        "Database SQLite sedang dikunci oleh proses lain. Tambahkan timeout busy_timeout atau tunggu proses lain selesai."
    ),
    DiagnosticRule(
        r"(?:error: Your local changes to the following files would be overwritten by merge|fatal: destination path '[^']+' already exists)",
        "Git State Conflict",
        "Ada konflik file git lokal. Pertimbangkan `git stash` sebelum pull, atau hapus direktori tujuan yang sudah ada."
    ),
    DiagnosticRule(
        r"(?:json\.decoder\.JSONDecodeError|Expecting value: line \d+ column \d+)",
        "Malformed JSON",
        "Format JSON tidak valid atau terpotong. Periksa tanda petik ganda dan kurung kurawal pembuka/penutup."
    )
]


class DiagnosticEngine:
    """Detects failure causes and injects remediation guidance into agent feedback."""

    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove ANSI escape sequences from terminal output."""
        return ANSI_REGEX.sub("", text)

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Scrub tokens, API keys, and sensitive auth data."""
        sanitized = text
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Strip ANSI and redact sensitive credentials."""
        return cls.redact_secrets(cls.strip_ansi(text))

    @classmethod
    def analyze_failure(
        cls,
        tool_name: str,
        output: str,
        exit_code: int = 1
    ) -> Optional[str]:
        """Inspect output and suggest actionable remediation hint if a known issue is matched."""
        clean_text = cls.strip_ansi(output)

        for rule in RULES:
            hint = rule.match(clean_text)
            if hint:
                return f"💡 **[Apex Diagnostic & Self-Healing - {rule.title}]**:\n{hint}"

        # Generic remediation hint for failed commands without explicit pattern
        if exit_code != 0 and len(output.strip()) > 0:
            return (
                "💡 **[Apex Diagnostic]**: Perintah/operasi keluar dengan status error (code != 0). "
                "Periksa pesan error di atas dan sesuaikan parameter sebelum mencoba kembali."
            )

        return None


# Global Diagnostic instance
diagnostic_engine = DiagnosticEngine()
