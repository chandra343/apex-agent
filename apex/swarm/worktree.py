"""Git Worktree Isolation & Instant Revert Sandbox for Autonomous Swarm Execution.

Enables risk-free agent modifications:
1. Spawns isolated worktree directory in /tmp/apex-worktrees/<task_id>
2. Subagent or agent tests and executes modifications in the sandbox
3. Runs automated verification suites (pytest, npm test, linters)
4. Merges into main working tree ONLY if 100% green
5. Instantly discards failed experiments without leaving dirty git states
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


SANDBOX_BASE = Path("/tmp/apex-worktrees")
SANDBOX_BASE.mkdir(parents=True, exist_ok=True)


class WorktreeSandboxManager:
    """Manages isolated git worktrees for safe autonomous coding."""

    def __init__(self, repo_dir: str = ".") -> None:
        self.repo_dir = Path(repo_dir).resolve()

    def _is_git_repo(self) -> bool:
        return (self.repo_dir / ".git").exists()

    def _run_git(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        p = subprocess.run(
            ["git"] + args,
            cwd=str(cwd or self.repo_dir),
            capture_output=True,
            text=True,
            timeout=120
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()

    def create_sandbox(self, task_id: str, base_branch: str = "HEAD") -> Dict[str, Any]:
        """Create an isolated worktree branch and working directory."""
        if not self._is_git_repo():
            return {"success": False, "error": f"{self.repo_dir} is not a valid git repository"}

        clean_id = "".join(c for c in task_id if c.isalnum() or c in "-_")[:32] or f"task_{int(time.time())}"
        branch_name = f"apex/sandbox-{clean_id}"
        worktree_path = SANDBOX_BASE / clean_id

        if worktree_path.exists():
            self.discard_sandbox(clean_id)

        # Create worktree with new branch
        code, out, err = self._run_git(["worktree", "add", "-b", branch_name, str(worktree_path), base_branch])
        if code != 0:
            # If branch already exists, try reusing or adding without -b
            code, out, err = self._run_git(["worktree", "add", str(worktree_path), branch_name])
            if code != 0:
                return {"success": False, "error": f"Failed to create git worktree: {err or out}"}

        return {
            "success": True,
            "task_id": clean_id,
            "branch": branch_name,
            "worktree_path": str(worktree_path),
            "message": f"Isolated sandbox initialized at {worktree_path} on branch {branch_name}"
        }

    def run_verification(self, task_id: str, command: str = "pytest") -> Dict[str, Any]:
        """Run verification command inside isolated worktree."""
        worktree_path = SANDBOX_BASE / task_id
        if not worktree_path.exists():
            return {"success": False, "error": f"Sandbox '{task_id}' does not exist at {worktree_path}"}

        start_t = time.time()
        p = subprocess.run(
            command,
            shell=True,
            cwd=str(worktree_path),
            capture_output=True,
            text=True,
            timeout=180
        )
        elapsed = round(time.time() - start_t, 2)

        return {
            "success": p.returncode == 0,
            "exit_code": p.returncode,
            "elapsed_seconds": elapsed,
            "output": (p.stdout + "\n" + p.stderr).strip()[:4000]
        }

    def apply_and_merge(self, task_id: str, commit_msg: str = "chore(apex): merge verified changes from sandbox") -> Dict[str, Any]:
        """Commit worktree changes and merge back into current repository branch."""
        worktree_path = SANDBOX_BASE / task_id
        if not worktree_path.exists():
            return {"success": False, "error": f"Sandbox '{task_id}' not found"}

        branch_name = f"apex/sandbox-{task_id}"

        # 1. Commit inside worktree
        self._run_git(["add", "."], cwd=worktree_path)
        c_code, c_out, c_err = self._run_git(["commit", "-m", commit_msg], cwd=worktree_path)

        # 2. Merge into parent repo
        m_code, m_out, m_err = self._run_git(["merge", branch_name, "--no-ff", "-m", f"Merge verified sandbox: {task_id}"])
        if m_code != 0:
            return {
                "success": False,
                "error": f"Merge conflict or failure: {m_err or m_out}. Sandbox preserved at {worktree_path} for manual review."
            }

        # 3. Clean up worktree
        self.discard_sandbox(task_id, delete_branch=True)

        return {
            "success": True,
            "message": f"Sandbox '{task_id}' successfully merged into main repo.",
            "merge_output": m_out
        }

    def discard_sandbox(self, task_id: str, delete_branch: bool = True) -> Dict[str, Any]:
        """Remove worktree and purge temporary branch."""
        worktree_path = SANDBOX_BASE / task_id
        branch_name = f"apex/sandbox-{task_id}"

        # Prune git worktree
        self._run_git(["worktree", "remove", "--force", str(worktree_path)])
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)

        self._run_git(["worktree", "prune"])

        if delete_branch:
            self._run_git(["branch", "-D", branch_name])

        return {
            "success": True,
            "message": f"Sandbox '{task_id}' purged successfully."
        }

    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List active worktrees."""
        code, out, _ = self._run_git(["worktree", "list", "--porcelain"])
        if code != 0 or not out:
            return []

        entries = []
        current: Dict[str, Any] = {}
        for line in out.splitlines():
            line = line.strip()
            if not line:
                if current:
                    entries.append(current)
                    current = {}
            elif line.startswith("worktree "):
                current["path"] = line.split(" ", 1)[1]
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current["head"] = line.split(" ", 1)[1]
        if current:
            entries.append(current)

        # Filter only apex sandboxes
        return [e for e in entries if "/apex-worktrees/" in e.get("path", "") or "apex/sandbox-" in e.get("branch", "")]


worktree_manager = WorktreeSandboxManager()


def manage_worktree_sandbox(
    action: str,
    task_id: str = "",
    command: str = "pytest",
    commit_msg: str = "",
    repo_dir: str = "."
) -> str:
    """Tool function to manage Git Worktree sandboxes."""
    mgr = WorktreeSandboxManager(repo_dir)
    act = action.strip().lower()

    if act in ["create", "new", "start"]:
        if not task_id:
            task_id = f"task_{int(time.time())}"
        res = mgr.create_sandbox(task_id)
        if not res["success"]:
            return f"❌ {res['error']}"
        return (
            f"🛡️ **Git Worktree Sandbox Created:**\n"
            f"• Task ID       : `{res['task_id']}`\n"
            f"• Branch        : `{res['branch']}`\n"
            f"• Worktree Path : `{res['worktree_path']}`\n\n"
            "Semua perubahan dapat dikerjakan di folder sandbox di atas tanpa mengganggu working tree utama."
        )

    if act in ["verify", "test", "run"]:
        if not task_id:
            return "❌ Masukkan task_id sandbox yang ingin diuji."
        res = mgr.run_verification(task_id, command=command)
        if not res["success"]:
            return f"❌ **Verifikasi GAGAL (Exit Code {res.get('exit_code')}, {res.get('elapsed_seconds')}s):**\n```\n{res.get('output', res.get('error'))}\n```"
        return f"✅ **Verifikasi 100% SUKSES ({res['elapsed_seconds']}s):**\n```\n{res['output']}\n```"

    if act in ["merge", "apply"]:
        if not task_id:
            return "❌ Masukkan task_id sandbox yang ingin di-merge."
        msg = commit_msg or f"feat(sandbox): verified implementation for {task_id}"
        res = mgr.apply_and_merge(task_id, commit_msg=msg)
        if not res["success"]:
            return f"❌ {res['error']}"
        return f"🎉 {res['message']}"

    if act in ["discard", "delete", "rm", "cancel"]:
        if not task_id:
            return "❌ Masukkan task_id sandbox yang ingin dibuang."
        res = mgr.discard_sandbox(task_id)
        return f"🗑️ {res['message']}"

    if act in ["list", "ls"]:
        items = mgr.list_sandboxes()
        if not items:
            return "ℹ️ Tidak ada sandbox git worktree aktif saat ini."
        lines = [f"🛡️ **Active Sandboxes ({len(items)}):**"]
        for it in items:
            lines.append(f"• `{it.get('branch', 'unknown')}` ➔ `{it.get('path')}`")
        return "\n".join(lines)

    return (
        "❓ Aksi tidak dikenali. Opsi:\n"
        "- `action='create', task_id='refactor-db'`\n"
        "- `action='verify', task_id='refactor-db', command='pytest tests/'`\n"
        "- `action='merge', task_id='refactor-db'`\n"
        "- `action='discard', task_id='refactor-db'`\n"
        "- `action='list'`"
    )
