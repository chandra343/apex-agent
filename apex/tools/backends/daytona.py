"""Daytona Cloud Development Environment Backend."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class DaytonaBackend:
    """Executes commands inside a Daytona remote workspace."""

    name = "daytona"

    def execute(
        self,
        command: str,
        cwd: Optional[Path | str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120
    ) -> Tuple[int, str, str]:
        cmd = ["daytona", "exec", "--", command]
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            return proc.returncode, proc.stdout, proc.stderr
        except Exception as e:
            return 1, "", f"Daytona execution error: {e}"
