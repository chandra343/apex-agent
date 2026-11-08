"""3-Button Interactive Approval Gate Engine (OpenClaw / Lobster Style)."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple
from apex.config import config

FATAL_PATTERNS = [
    r"rm\s+-r[fF]\s+[/~]",
    r"mkfs",
    r"dd\s+if=",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",  # forkbomb
    r">/dev/sd[a-z]",
    r"shutdown",
    r"reboot",
    r"init\s+0",
    r"chmod\s+-R\s+777\s+/",
    r"drop\s+database",
    r"truncate\s+table"
]


class ApprovalGate:
    """Detects critical commands and guards execution behind interactive human confirmation."""

    def __init__(self) -> None:
        self._always_allowed_patterns: Set[str] = set()

    def is_fatal_command(self, command: str) -> bool:
        """Check if a shell command matches any high-risk fatal pattern."""
        cmd_clean = command.strip()
        for pat in self._always_allowed_patterns:
            if re.search(pat, cmd_clean, re.IGNORECASE):
                return False

        for pat in FATAL_PATTERNS:
            if re.search(pat, cmd_clean, re.IGNORECASE):
                return True
        return False

    def check_approval_needed(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if an impending tool invocation requires user confirmation."""
        mode = config.get("security.approval_mode", "interactive")
        if mode == "always" or not config.get("security.require_approval_on_fatal_commands", True):
            return False, ""

        if tool_name == "run_shell":
            cmd = arguments.get("command", "")
            if self.is_fatal_command(cmd):
                return True, f"Dangerous command detected: `{cmd}`"

        return False, ""

    def approve_always(self, pattern: str) -> None:
        """Mark pattern as always approved for this session (⚡ Selalu Eksekusi)."""
        self._always_allowed_patterns.add(pattern.strip())


# Global approval gate instance
approval_gate = ApprovalGate()
