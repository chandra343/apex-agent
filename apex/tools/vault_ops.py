"""Tools for interacting with the Apex Encrypted Secret Vault."""
from __future__ import annotations

import json
from typing import Any, Dict
from apex.security.vault import secret_vault


def manage_vault(
    action: str,
    key: str = "",
    value: str = "",
    description: str = ""
) -> str:
    """Manage encrypted credentials, API keys, and sensitive tokens in the Apex Vault.

    Args:
        action: One of 'set', 'get', 'list', 'delete'.
        key: The uppercase name of the secret (e.g. 'AWS_SECRET_KEY', 'DATABASE_PASSWORD').
        value: The secret plaintext value (required for 'set').
        description: Optional human-readable description of what this secret is for.

    Returns:
        Structured result string or Markdown status.
    """
    act = action.strip().lower()

    if act == "set":
        if not key or not value:
            return "❌ Parameter 'key' dan 'value' wajib diisi untuk action 'set'."
        ok = secret_vault.set(key, value, description=description)
        if ok:
            return f"🔐 Sukses menyimpan secret `{key.upper()}` ke dalam Encrypted Vault (AES-256-GCM)."
        return f"❌ Gagal menyimpan secret `{key}`."

    elif act == "get":
        if not key:
            return "❌ Parameter 'key' wajib diisi untuk action 'get'."
        val = secret_vault.get(key)
        if val is None:
            return f"⚠️ Secret `{key.upper()}` tidak ditemukan di dalam Vault."
        return f"🔑 Secret `{key.upper()}`: `{val}`"

    elif act == "list":
        keys = secret_vault.list_keys()
        if not keys:
            return "📭 Apex Vault saat ini kosong. Belum ada secret yang tersimpan."
        rows = [
            "| Key | Masked Value | Deskripsi | Diperbarui |",
            "| --- | --- | --- | --- |"
        ]
        for k in keys:
            dt = ""
            if k.get("updated_at"):
                import datetime
                dt = datetime.datetime.fromtimestamp(k["updated_at"]).strftime("%Y-%m-%d %H:%M")
            rows.append(f"| `{k['key']}` | `{k['masked']}` | {k.get('description') or '-'} | {dt} |")
        return "🔐 **Apex Encrypted Vault Inventory**:\n\n" + "\n".join(rows)

    elif act == "delete":
        if not key:
            return "❌ Parameter 'key' wajib diisi untuk action 'delete'."
        ok = secret_vault.delete(key)
        if ok:
            return f"🗑️ Secret `{key.upper()}` telah dihapus dari Vault."
        return f"⚠️ Secret `{key.upper()}` tidak ditemukan di dalam Vault."

    else:
        return f"❌ Action `{action}` tidak dikenal. Gunakan: 'set', 'get', 'list', atau 'delete'."
