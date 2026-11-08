"""Cross-platform process helpers for Windows and POSIX."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
from typing import Any

IS_WINDOWS = sys.platform == "win32"


def get_subprocess_flags() -> dict[str, Any]:
    """Return process creation flags suitable for the current platform."""
    flags: dict[str, Any] = {}
    if IS_WINDOWS:
        # Prevent popup console windows and allow graceful process tree termination
        CREATE_NO_WINDOW = 0x08000000
        flags["creationflags"] = CREATE_NO_WINDOW
    return flags


def kill_process_tree(pid: int) -> None:
    """Terminate a process and all its child subprocesses gracefully."""
    if IS_WINDOWS:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
