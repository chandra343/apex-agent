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

    elif act == "profile_list":
        profiles = config.list_profiles()
        lines = ["🗂️ **Daftar Profil Konfigurasi Apex**:"]
        for p in profiles:
            mark = "★ **(AKTIF)**" if p.get("active") else ""
            lines.append(f"• `{p.get('name')}` {mark} — Model: `{p.get('model')}`, Provider: `{p.get('provider')}`")
        return "\n".join(lines)

    elif act == "profile_use":
        target = (value or key_path or "").strip()
        if not target:
            return "❌ Tentukan nama profil dalam parameter `value`."
        if config.load_profile(target):
            return f"✅ **Berhasil Beralih ke Profil `{target}`**. Model default sekarang: `{config.default_model}`."
        return f"❌ Profil `{target}` tidak ditemukan."

    elif act == "profile_save":
        target = (value or key_path or "").strip()
        if not target:
            return "❌ Tentukan nama profil dalam parameter `value`."
        if config.save_profile(target):
            return f"✅ **Konfigurasi Saat Ini Berhasil Disimpan sebagai Profil `{target}`**."
        return f"❌ Gagal menyimpan profil `{target}`."

    elif act == "validate":
        report = config.validate_config()
        status_icon = "✅" if report.get("valid") else "⚠️"
        lines = [f"{status_icon} **Hasil Validasi Konfigurasi & Setup (Profil: `{report.get('profile')}`)**:"]
        for c in report.get("checks", []):
            st = c.get("status")
            badge = "PASS" if st == "PASS" else ("WARN" if st == "WARN" else "FAIL")
            path_val = c.get("path") or c.get("model") or ""
            lines.append(f"• [{badge}] **{c.get('item')}**: `{path_val}`")
        issues = report.get("issues", [])
        if issues:
            lines.append("\n**Catatan Masalah:**")
            for iss in issues:
                lines.append(f"  - ⚠️ {iss}")
        return "\n".join(lines)

    elif act == "sync_env":
        updated = config.sync_environment_keys()
        if updated:
            return f"✅ **Kredensial Berhasil Disinkronkan dari Environment**: {', '.join(updated)}."
        return "ℹ️ Tidak ada kredensial baru atau yang berbeda dari environment saat ini."

    return f"❌ Aksi '{action}' tidak dikenali. Gunakan 'list', 'get', 'set', 'profile_list', 'profile_use', 'profile_save', 'validate', atau 'sync_env'."
