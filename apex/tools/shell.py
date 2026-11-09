"""Shell execution interface with background process tracking and daemon management."""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from apex._winproc import get_subprocess_flags, kill_process_tree
from apex.tools.backends import backend_manager
from apex.diagnostics.engine import diagnostic_engine
from apex.security.vault import secret_vault


class BackgroundProcessTracker:
    """Tracks background processes spawned by the agent."""

    def __init__(self) -> None:
        self._procs: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register(self, proc: subprocess.Popen, command: str) -> None:
        with self._lock:
            self._procs[proc.pid] = {
                "process": proc,
                "command": command,
                "start_time": time.time(),
                "output_buffer": []
            }
        # Start background output reader thread
        threading.Thread(target=self._reader_worker, args=(proc.pid,), daemon=True).start()

    def _reader_worker(self, pid: int) -> None:
        proc_data = self._procs.get(pid)
        if not proc_data:
            return
        proc = proc_data["process"]
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                with self._lock:
                    proc_data["output_buffer"].append(line)
                    if len(proc_data["output_buffer"]) > 500:
                        proc_data["output_buffer"].pop(0)
        except Exception:
            pass

    def list_processes(self) -> List[Dict[str, Any]]:
        with self._lock:
            active = []
            for pid, d in list(self._procs.items()):
                proc = d["process"]
                poll = proc.poll()
                is_running = poll is None
                active.append({
                    "pid": pid,
                    "command": d["command"],
                    "running": is_running,
                    "exit_code": poll,
                    "elapsed_seconds": round(time.time() - d["start_time"], 1)
                })
            return active

    def get_output(self, pid: int, lines: int = 50) -> Optional[str]:
        with self._lock:
            if pid not in self._procs:
                return None
            buffer = self._procs[pid]["output_buffer"]
            return "".join(buffer[-lines:])

    def kill_process(self, pid: int) -> bool:
        with self._lock:
            if pid not in self._procs:
                return False
            kill_process_tree(pid)
            return True


# Global background tracker
bg_tracker = BackgroundProcessTracker()


def run_shell(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 120,
    background: bool = False,
    backend_override: Optional[str] = None
) -> Tuple[int, str]:
    """Execute a terminal command synchronously or in the background."""
    work_dir = Path(cwd).resolve() if cwd else Path.cwd()
    resolved_cmd = secret_vault.resolve_placeholders(command)

    if background:
        flags = get_subprocess_flags()
        try:
            proc = subprocess.Popen(
                resolved_cmd,
                shell=True,
                cwd=str(work_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                **flags
            )
            bg_tracker.register(proc, command)
            return 0, f"Background process started with PID: {proc.pid}\nCommand: {command}"
        except Exception as e:
            return 1, f"Failed to start background process: {e}"

    # Synchronous execution through backend
    code, stdout, stderr = backend_manager.execute(
        command=resolved_cmd,
        cwd=work_dir,
        timeout=timeout,
        backend_override=backend_override
    )

    combined = ""
    if stdout:
        combined += stdout
    if stderr:
        if combined and not combined.endswith("\n"):
            combined += "\n"
        combined += "[STDERR]\n" + stderr

    # Sanitize ANSI escapes and scrub credentials
    clean_output = diagnostic_engine.sanitize(combined.strip())

    # Auto-remediation diagnostic hint
    if code != 0:
        hint = diagnostic_engine.analyze_failure("run_shell", clean_output, exit_code=code)
        if hint:
            clean_output += f"\n\n{hint}"

    return code, clean_output
