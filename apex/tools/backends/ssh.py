"""Remote SSH Execution Backend: Executes commands on a remote server/VPS."""
from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class SSHBackend:
    """Executes commands over SSH on a remote host."""

    name = "ssh"

    def __init__(self, host: str = "localhost", user: Optional[str] = None, port: int = 22, key_path: Optional[str] = None) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path

    def execute(
        self,
        command: str,
        cwd: Optional[Path | str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120
    ) -> Tuple[int, str, str]:
        """Wrap command in ssh and execute remotely."""
        ssh_cmd = ["ssh", "-p", str(self.port), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new"]
        
        if self.key_path:
            ssh_cmd.extend(["-i", self.key_path])

        target = f"{self.user}@{self.host}" if self.user else self.host
        ssh_cmd.append(target)

        # Build remote command string with cwd and env
        remote_parts: list[str] = []
        if cwd:
            remote_parts.append(f"cd {shlex.quote(str(cwd))}")
        if env:
            for k, v in env.items():
                remote_parts.append(f"export {k}={shlex.quote(v)}")
        remote_parts.append(command)

        remote_script = " && ".join(remote_parts)
        ssh_cmd.append(remote_script)

        try:
            proc = subprocess.run(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"SSH command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)
