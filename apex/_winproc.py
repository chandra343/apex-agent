"""Cross-platform process helpers for Windows and POSIX."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from typing import Any

IS_WINDOWS = sys.platform == "win32"


def get_subprocess_flags() -> dict[str, Any]:
    """Return process creation flags suitable for the current platform."""
    flags: dict[str, Any] = {}
    if IS_WINDOWS:
        # Prevent popup console windows and allow graceful process tree termination
        CREATE_NO_WINDOW = 0x08000000
        flags["creationflags"] = CREATE_NO_WINDOW
    else:
        # Isolate child into its own process group so terminating children never kills Apex
        flags["start_new_session"] = True
    return flags


def kill_process_tree(pid: int) -> None:
    """Terminate a process and all its child subprocesses gracefully without killing parent."""
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
            target_pgid = os.getpgid(pid)
            current_pgid = os.getpgid(0)
            # NEVER kill own process group!
            if target_pgid != current_pgid and target_pgid > 1:
                os.killpg(target_pgid, signal.SIGTERM)
                time.sleep(0.1)
                try:
                    os.killpg(target_pgid, signal.SIGKILL)
                except Exception:
                    pass
            else:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
