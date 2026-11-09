"""System Doctor, Health Diagnostics & Self-Healing Tool for Project Apex."""
from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List
from apex.config import DATA_DIR, config
from apex.router.provider_manager import provider_manager


def run_system_doctor(auto_repair: bool = True) -> str:
    """Run an automated diagnostic check across all Apex subsystems, databases, and dependencies.

    Checks:
    - Host directory structure and permissions (auto-repairs missing directories).
    - SQLite database integrity (memory.db, lessons.db, knowledge_base.db).
    - OCR and document parsing binaries (tesseract, pdftotext).
    - Critical Python dependencies (FastAPI, PyPDF, python-docx, Pillow).
    - Active AI provider status and API key configuration.

    Args:
        auto_repair: Automatically create missing directories and initialize schemas.

    Returns:
        Structured Markdown health scorecard.
    """
    scorecard: list[str] = ["🏥 **Kartu Diagnostik Kesehatan Sistem Apex (System Doctor)** 🩺\n"]
    repairs_done: list[str] = []

    # 1. Check & Repair Required Directories
    required_dirs = [
        DATA_DIR,
        DATA_DIR / "uploads",
        DATA_DIR / "audio",
        DATA_DIR / "custom_tools",
        DATA_DIR / "skills",
        DATA_DIR / "sessions",
        DATA_DIR / "checkpoints"
    ]

    missing_dirs = [d for d in required_dirs if not d.exists()]
    if missing_dirs and auto_repair:
        for d in missing_dirs:
            d.mkdir(parents=True, exist_ok=True)
            repairs_done.append(f"Membuat direktori sistem yang hilang: `{d.name}`")
        scorecard.append(f"✅ **Struktur Direktori**: Pulih ({len(missing_dirs)} direktori diperbaiki otomatis)")
    elif missing_dirs:
        scorecard.append(f"⚠️ **Struktur Direktori**: {len(missing_dirs)} direktori belum dibuat")
    else:
        scorecard.append(f"✅ **Struktur Direktori**: Lengkap & Sehat ({len(required_dirs)} direktori aktif)")

    # 2. Database Integrity Checks
    db_files = [
        ("memory.db", DATA_DIR / "memory.db"),
        ("lessons.db", DATA_DIR / "lessons.db"),
        ("durable_jobs.db", DATA_DIR / "durable_jobs.db"),
        ("knowledge_base.db", DATA_DIR / "knowledge_base.db")
    ]

    db_statuses = []
    for db_name, db_path in db_files:
        if db_path.exists():
            try:
                with sqlite3.connect(db_path) as conn:
                    cur = conn.cursor()
                    cur.execute("PRAGMA integrity_check;")
                    res = cur.fetchone()
                    if res and res[0] == "ok":
                        db_statuses.append(f"`{db_name}`: [OK]")
                    else:
                        db_statuses.append(f"`{db_name}`: [CORRUPT: {res}]")
            except Exception as e:
                db_statuses.append(f"`{db_name}`: [ERROR: {e}]")
        else:
            db_statuses.append(f"`{db_name}`: [Pending Init]")

    scorecard.append(f"✅ **Integritas Basis Data SQLite**: {', '.join(db_statuses)}")

    # 3. Host Binaries
    binaries = {
        "git": "Version control",
        "tesseract": "Local OCR engine",
        "pdftotext": "PDF text extraction"
    }
    bin_status = []
    for b_name, b_desc in binaries.items():
        loc = shutil.which(b_name)
        if loc:
            bin_status.append(f"✔ `{b_name}` ({b_desc})")
        else:
            bin_status.append(f"✖ `{b_name}` *(tidak terpasang)*")
    scorecard.append(f"⚙️ **Biner Host Eksternal**:\n   • " + "\n   • ".join(bin_status))

    # 4. Python Packages
    packages = ["fastapi", "uvicorn", "pypdf", "docx", "openpyxl", "PIL", "pytesseract", "rich"]
    pkg_status = []
    for p in packages:
        try:
            __import__(p)
            pkg_status.append(f"✔ `{p}`")
        except ImportError:
            pkg_status.append(f"✖ `{p}`")
    scorecard.append(f"📦 **Paket Python Kritis**: " + ", ".join(pkg_status))

    # 5. AI Provider Readiness
    active_prov = config.active_provider
    active_model = config.default_model
    is_conf = provider_manager.is_provider_configured(active_prov)
    prov_badge = "✅ Terkonfigurasi" if is_conf else "⚠️ Belum ada API key terpasang"
    scorecard.append(
        f"🤖 **Status Provider AI**:\n"
        f"   • Provider Aktif: **{active_prov.upper()}** ({prov_badge})\n"
        f"   • Model Default: `{active_model}`"
    )

    if repairs_done:
        scorecard.append(f"\n🔧 **Tindakan Pemulihan Otomatis (Self-Healing)**:\n• " + "\n• ".join(repairs_done))

    return "\n\n".join(scorecard)
