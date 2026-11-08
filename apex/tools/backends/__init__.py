"""Modular Execution Backends Registry and Switcher (Hermes Style)."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from pathlib import Path
from apex.config import config
from apex.tools.backends.local import LocalBackend, local_backend
from apex.tools.backends.docker import DockerBackend
from apex.tools.backends.ssh import SSHBackend
from apex.tools.backends.modal import ModalBackend
from apex.tools.backends.daytona import DaytonaBackend

BACKENDS: Dict[str, Any] = {
    "local": local_backend,
    "docker": DockerBackend(),
    "ssh": SSHBackend(),
    "modal": ModalBackend(),
    "daytona": DaytonaBackend()
}


class BackendManager:
    """Manages active execution backend and provides runtime /backend switching."""

    def __init__(self) -> None:
        pass

    @property
    def active_backend_name(self) -> str:
        return config.get("active_backend", "local")

    def get_backend(self, name: Optional[str] = None) -> Any:
        backend_name = name or self.active_backend_name
        return BACKENDS.get(backend_name.lower(), local_backend)

    def switch_backend(self, name: str) -> Tuple[bool, str]:
        """Switch active execution backend at runtime."""
        target = name.strip().lower()
        if target not in BACKENDS:
            return False, f"Unknown backend '{name}'. Available: {', '.join(BACKENDS.keys())}"
        config.set("active_backend", target, auto_save=True)
        return True, f"Switched execution backend to: '{target}'"

    def execute(
        self,
        command: str,
        cwd: Optional[Path | str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        backend_override: Optional[str] = None
    ) -> Tuple[int, str, str]:
        """Execute command using currently selected backend."""
        backend = self.get_backend(backend_override)
        return backend.execute(command=command, cwd=cwd, env=env, timeout=timeout)


# Global backend manager instance
backend_manager = BackendManager()
