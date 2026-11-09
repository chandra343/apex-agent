"""System Configuration Inspection & Tuning Tool for Project Apex."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from apex.config import config


def manage_system_config(
    action: str,
    key_path: Optional[str] = None,
    value: Optional[str] = None
) -> str:
    """Inspect or update Project Apex system settings dynamically.

    Supported key paths:
    - 'default_model': Active default AI model
    - 'active_provider': Default provider ID (e.g. 'tokenharbor', 'deepseek', 'ollama')
    - 'router.rtk_compression': Enable/disable RTK token saver (true/false)
    - 'router.rtk_threshold_bytes': Minimum bytes before compression
    - 'security.pairing_code': Telegram pairing secret code
    - 'fallback_tiers.tier_2_cheap': List of secondary backup models

    Args:
        action: 'get' to inspect, 'set' to update, or 'list' for high-level overview.
        key_path: Nested key path with dot notation (e.g. 'default_model', 'router.rtk_compression').
        value: New value to assign when action is 'set' (supports strings, booleans, or JSON).

    Returns:
        Structured confirmation or inspection results.
    """
    act = action.strip().lower()

    if act == "list":
        active_m = config.default_model
        active_p = config.active_provider
        rtk = config.get("router.rtk_compression", True)
        return (
            f"⚙️ **Ikhtisar Konfigurasi Sistem Apex**:\n\n"
            f"• Model Default: `{active_m}` (Provider: `{active_p}`)\n"
            f"• Backend Host: `{config.active_backend}`\n"
            f"• RTK Token Compression: **{'Aktif' if rtk else 'Nonaktif'}**\n"
            f"• Workspace: `{config.workspace}`\n"
            f"• Telegram Gateways: `{', '.join(config.get('gateways.enabled', []))}`"
        )

    elif act == "get":
        if not key_path:
            return "❌ Parameter `key_path` wajib diisi saat melakukan 'get'."
        val = config.get(key_path)
        if val is None:
            return f"⚠️ Key `{key_path}` tidak ditemukan dalam konfigurasi."
        if isinstance(val, (dict, list)):
            return f"⚙️ **Konfigurasi `{key_path}`**:\n```json\n{json.dumps(val, indent=2)}\n```"
        return f"⚙️ **Konfigurasi `{key_path}`**: `{val}`"

    elif act == "set":
        if not key_path or value is None:
            return "❌ Parameter `key_path` dan `value` wajib diisi saat melakukan 'set'."

        parsed_val: Any = value
        try:
            parsed_val = json.loads(value)
        except Exception:
            if value.lower() == "true":
                parsed_val = True
            elif value.lower() == "false":
                parsed_val = False

        config.set(key_path, parsed_val)
        return f"✅ **Konfigurasi Berhasil Diperbarui**: `{key_path}` = `{parsed_val}` (Tersimpan di disk)."

    return f"❌ Aksi '{action}' tidak dikenali. Gunakan 'list', 'get', atau 'set'."
