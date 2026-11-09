"""DevOps CI/CD Suite & Automated Test Runner for Project Apex."""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from apex.tools.shell import run_shell


def run_project_tests(
    path: str = ".",
    framework: Optional[str] = None,
    timeout: int = 120
) -> str:
    """Auto-detect and execute the test suite for a project, returning structured pass/fail diagnostics.

    Supports:
    - Python: pytest / unittest
    - Node.js: npm test / jest / vitest
    - Go: go test ./...
    - Rust: cargo test

    Args:
        path: Root directory of the project (default: '.').
        framework: Optional explicit framework override ('pytest', 'npm', 'go', 'cargo').
        timeout: Maximum execution timeout in seconds (default: 120).

    Returns:
        Structured test execution report with failure stack traces if any.
    """
    proj_dir = Path(os.path.expanduser(path)).resolve()
    if not proj_dir.exists():
        return f"❌ Direktori proyek tidak ditemukan: `{path}`"

    # Auto-detection
    test_cmd = ""
    detected_fw = ""

    if framework:
        fw_clean = framework.lower().strip()
        if fw_clean in ["pytest", "python"]:
            # Check for virtual environment pytest first
            venv_pytest = proj_dir / ".venv" / "bin" / "pytest"
            test_cmd = f"{venv_pytest} -v" if venv_pytest.exists() else "pytest -v"
            detected_fw = "Python (pytest)"
        elif fw_clean in ["npm", "node", "jest"]:
            test_cmd = "npm test"
            detected_fw = "Node.js (npm test)"
        elif fw_clean in ["go", "golang"]:
            test_cmd = "go test -v ./..."
            detected_fw = "Go (go test)"
        elif fw_clean in ["cargo", "rust"]:
            test_cmd = "cargo test"
            detected_fw = "Rust (cargo test)"
        else:
            test_cmd = framework
            detected_fw = f"Custom ({framework})"
    else:
        # Detect based on project markers
        venv_pytest = proj_dir / ".venv" / "bin" / "pytest"
        if (proj_dir / "pyproject.toml").exists() or (proj_dir / "tests").exists() or (proj_dir / "setup.py").exists():
            test_cmd = f"{venv_pytest} -v" if venv_pytest.exists() else "pytest -v"
            detected_fw = "Python (pytest)"
        elif (proj_dir / "package.json").exists():
            test_cmd = "npm test"
            detected_fw = "Node.js (npm test)"
        elif (proj_dir / "Cargo.toml").exists():
            test_cmd = "cargo test"
            detected_fw = "Rust (cargo test)"
        elif (proj_dir / "go.mod").exists():
            test_cmd = "go test -v ./..."
            detected_fw = "Go (go test)"
        else:
            test_cmd = f"{venv_pytest} -v" if venv_pytest.exists() else "pytest -v"
            detected_fw = "Python (default fallback)"

    start_t = time.time()
    code, output = run_shell(test_cmd, cwd=str(proj_dir), timeout=timeout)
    elapsed = round(time.time() - start_t, 2)

    status_icon = "✅ LULUS" if code == 0 else "❌ GAGAL"
    badge_style = "✅" if code == 0 else "🚨"

    lines = output.splitlines()
    summary_lines = []
    # Capture failure lines or summary lines
    for l in lines:
        if any(kw in l for kw in ["passed", "failed", "error", "FAIL", "PASS", "ERR", "test session starts"]):
            summary_lines.append(l)

    output_preview = "\n".join(lines[-35:]) if len(lines) > 35 else output

    return (
        f"{badge_style} **Laporan Hasil Pengujian Proyek ({status_icon})** 🧪\n\n"
        f"• Framework: **{detected_fw}**\n"
        f"• Perintah: `{test_cmd}`\n"
        f"• Direktori: `{proj_dir}`\n"
        f"• Durasi: **{elapsed}s** (Exit Code: {code})\n\n"
        f"### 📋 Output Pengujian:\n"
        f"```\n{output_preview}\n```"
    )


def create_git_patch(
    branch_name: Optional[str] = None,
    commit_message: Optional[str] = None
) -> str:
    """Create a new Git branch, stage working changes, and synthesize a clean commit or patch.

    Args:
        branch_name: Optional new branch to create and checkout (e.g. 'feat/new-auth').
        commit_message: Optional commit message to commit staged changes.

    Returns:
        Summary of git operations and diff summary.
    """
    ops_log = []

    # 1. Branch checkout if requested
    if branch_name:
        code, out = run_shell(f"git checkout -b {branch_name}")
        if code != 0:
            # Fallback checkout existing
            code, out = run_shell(f"git checkout {branch_name}")
        ops_log.append(f"Branch: `{branch_name}` ({out.strip() or 'active'})")

    # 2. Check diff
    code, diff_out = run_shell("git status --short")
    if not diff_out.strip():
        return "ℹ️ Tidak ada perubahan file di direktori kerja Git (*clean working tree*)."

    # 3. Stage and commit if requested
    if commit_message:
        run_shell("git add .")
        code, commit_out = run_shell(f"git commit -m '{commit_message}'")
        if code == 0:
            ops_log.append(f"✅ Commit Berhasil: *\"{commit_message}\"*")
        else:
            ops_log.append(f"⚠️ Commit Error: {commit_out.strip()}")

    # 4. Generate summary
    code, stat_out = run_shell("git diff --stat HEAD~1 HEAD" if commit_message else "git diff --stat")
    return (
        f"🌿 **Operasi Git DevOps Selesai** 🚀\n\n"
        + "\n".join(f"• {log}" for log in ops_log) + "\n\n"
        f"```\n{stat_out.strip() or diff_out.strip()}\n```"
    )
