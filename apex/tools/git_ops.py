"""Native Git Integration Suite."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Tuple


def _run_git(args: list[str], cwd: Optional[str] = None) -> Tuple[int, str]:
    work_dir = Path(cwd).resolve() if cwd else Path.cwd()
    cmd = ["git"] + args
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        output = proc.stdout if proc.returncode == 0 else f"{proc.stdout}\n{proc.stderr}".strip()
        return proc.returncode, output
    except Exception as e:
        return 1, f"Git error: {e}"


def git_status(cwd: Optional[str] = None) -> Tuple[bool, str]:
    """Get current working tree status."""
    code, out = _run_git(["status", "--short", "--branch"], cwd)
    return code == 0, out or "Clean working directory"


def git_diff(staged: bool = False, cwd: Optional[str] = None) -> Tuple[bool, str]:
    """Show changes in working directory or staged index."""
    args = ["diff", "--cached"] if staged else ["diff"]
    code, out = _run_git(args, cwd)
    return code == 0, out or "No changes detected"


def git_commit(message: str, all_files: bool = True, cwd: Optional[str] = None) -> Tuple[bool, str]:
    """Stage and commit changes with a commit message."""
    if all_files:
        code_add, out_add = _run_git(["add", "-A"], cwd)
        if code_add != 0:
            return False, f"Failed to stage files: {out_add}"

    code_commit, out_commit = _run_git(["commit", "-m", message], cwd)
    return code_commit == 0, out_commit


def git_log(count: int = 10, cwd: Optional[str] = None) -> Tuple[bool, str]:
    """View recent commit history."""
    args = ["log", f"-{count}", "--oneline", "--decorate"]
    code, out = _run_git(args, cwd)
    return code == 0, out or "No commits found"


def git_branch(cwd: Optional[str] = None) -> Tuple[bool, str]:
    """List local branches."""
    code, out = _run_git(["branch", "-a"], cwd)
    return code == 0, out
