"""Docker Sandbox Backend: Isolates execution inside a Docker container."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class DockerBackend:
    """Executes commands inside a container to isolate risky or untrusted code."""

    name = "docker"

    def __init__(self, image: str = "python:3.11-slim") -> None:
        self.image = image

    def execute(
        self,
        command: str,
        cwd: Optional[Path | str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120
    ) -> Tuple[int, str, str]:
        """Wrap command in docker run and execute."""
        host_workdir = str(cwd) if cwd else str(Path.cwd())
        
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{host_workdir}:/workspace",
            "-w", "/workspace",
        ]

        if env:
            for k, v in env.items():
                docker_cmd.extend(["-e", f"{k}={v}"])

        docker_cmd.extend([self.image, "sh", "-c", command])

        try:
            proc = subprocess.run(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Docker execution timed out after {timeout} seconds"
        except FileNotFoundError:
            return 127, "", "Docker executable not found on host. Is Docker installed?"
        except Exception as e:
            return 1, "", str(e)
