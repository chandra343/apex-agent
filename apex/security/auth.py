"""Binary Authorization & Pairing Code Security Layer."""
from __future__ import annotations

from typing import Any, List
from apex.config import config


class SecurityAuth:
    """Manages owner allowlist and pairing code authorization."""

    def __init__(self) -> None:
        pass

    def is_authorized(self, user_or_chat_id: str | int) -> bool:
        """Check if user/chat ID is in the owner allowlist."""
        uid_str = str(user_or_chat_id).strip()
        owners = [str(o).strip() for o in config.get("security.owner_ids", [])]
        allowed_chats = [str(c).strip() for c in config.get("gateways.telegram.allowed_chats", [])]

        return uid_str in owners or uid_str in allowed_chats

    def try_pairing(self, user_or_chat_id: str | int, entered_code: str) -> bool:
        """Attempt to authorize a new user/chat with the secret pairing code."""
        configured_code = config.get("security.pairing_code", "APEX-2026").strip()
        if not entered_code or entered_code.strip() != configured_code:
            return False

        uid_str = str(user_or_chat_id).strip()
        
        # Add to owners list
        owners = config.get("security.owner_ids", [])
        if uid_str not in [str(o) for o in owners]:
            owners.append(uid_str)
            config.set("security.owner_ids", owners, auto_save=False)

        # Add to telegram allowed chats
        chats = config.get("gateways.telegram.allowed_chats", [])
        if uid_str not in [str(c) for c in chats]:
            chats.append(uid_str)
            config.set("gateways.telegram.allowed_chats", chats, auto_save=False)

        config.save()
        return True


# Global auth instance
security_auth = SecurityAuth()
