"""Local Host Execution Backend (Default: 100% Unrestricted Host Access)."""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from apex._winproc import get_subprocess_flags, kill_process_tree


class LocalBackend:
    """Executes commands directly on the host operating system."""

    name = "local"

    def execute(
        self,
        command: str,
        cwd: Optional[Path | str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120
    ) -> Tuple[int, str, str]:
        """Run a command synchronously on the host.

        Returns:
            Tuple[exit_code: int, stdout: str, stderr: str]
        """
        work_dir = str(cwd) if cwd else os.getcwd()
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        flags = get_subprocess_flags()

        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=work_dir,
                env=full_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **flags
            )
            stdout, stderr = proc.communicate(timeout=timeout)
            return proc.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            kill_process_tree(proc.pid)
            return 124, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)


# Default local instance
local_backend = LocalBackend()
