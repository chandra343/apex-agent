"""Encrypted Secret Vault & Credential Storage using AES-256-GCM (OpenBot & Bitwarden Style)."""
from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from apex.config import APEX_DIR, config


VAULT_FILE = APEX_DIR / "vault.enc"
VAULT_SALT_FILE = APEX_DIR / ".vault_salt"


class SecretVault:
    """Enterprise-grade AES-256-GCM Encrypted Vault for API Keys, Passwords, and Tokens."""

    def __init__(self, vault_path: Optional[Path] = None, salt_path: Optional[Path] = None) -> None:
        self.vault_path = vault_path or VAULT_FILE
        self.salt_path = salt_path or VAULT_SALT_FILE
        self._key: Optional[bytes] = None

    def _get_or_create_salt(self) -> bytes:
        if self.salt_path.exists():
            try:
                return self.salt_path.read_bytes()
            except Exception:
                pass
        self.salt_path.parent.mkdir(parents=True, exist_ok=True)
        salt = os.urandom(32)
        try:
            self.salt_path.write_bytes(salt)
            self.salt_path.chmod(0o600)
        except Exception:
            pass
        return salt

    def _derive_key(self) -> bytes:
        if self._key is not None:
            return self._key

        salt = self._get_or_create_salt()
        passphrase = config.get("security.vault_passphrase") or "apex-sovereign-vault-2026-default"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        self._key = kdf.derive(passphrase.encode("utf-8"))
        return self._key

    def _load_vault(self) -> Dict[str, Any]:
        if not self.vault_path.exists():
            return {"version": 1, "entries": {}}
        try:
            with open(self.vault_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "entries" in data:
                    return data
        except Exception:
            pass
        return {"version": 1, "entries": {}}

    def _save_vault(self, data: Dict[str, Any]) -> None:
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        try:
            self.vault_path.chmod(0o600)
        except Exception:
            pass

    @staticmethod
    def _mask_value(val: str) -> str:
        if len(val) <= 6:
            return "******"
        return f"{val[:3]}...{val[-3:]}"

    def set(self, key: str, value: str, description: str = "") -> bool:
        """Encrypt and store a secret."""
        key = key.strip().upper()
        if not key or not value:
            return False

        derived_key = self._derive_key()
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), key.encode("utf-8"))

        data = self._load_vault()
        now = time.time()
        existing = data["entries"].get(key, {})

        data["entries"][key] = {
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
            "description": description or existing.get("description", ""),
            "masked": self._mask_value(value),
            "created_at": existing.get("created_at", now),
            "updated_at": now
        }
        self._save_vault(data)
        return True

    def get(self, key: str) -> Optional[str]:
        """Decrypt and return a secret value."""
        key = key.strip().upper()
        data = self._load_vault()
        entry = data["entries"].get(key)
        if not entry:
            return None

        try:
            nonce = base64.b64decode(entry["nonce"])
            ciphertext = base64.b64decode(entry["ciphertext"])
            derived_key = self._derive_key()
            aesgcm = AESGCM(derived_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, key.encode("utf-8"))
            return plaintext.decode("utf-8")
        except Exception:
            return None

    def list_keys(self) -> List[Dict[str, Any]]:
        """List all stored secret keys with masked previews (never plaintext)."""
        data = self._load_vault()
        results = []
        for key, entry in sorted(data["entries"].items()):
            results.append({
                "key": key,
                "masked": entry.get("masked", "******"),
                "description": entry.get("description", ""),
                "created_at": entry.get("created_at"),
                "updated_at": entry.get("updated_at")
            })
        return results

    def delete(self, key: str) -> bool:
        """Remove a secret from the vault."""
        key = key.strip().upper()
        data = self._load_vault()
        if key in data["entries"]:
            del data["entries"][key]
            self._save_vault(data)
            return True
        return False

    def resolve_placeholders(self, text: str) -> str:
        """Replace {{vault:KEY}} placeholders with decrypted values."""
        pattern = re.compile(r"\{\{vault:([A-Za-z0-9_-]+)\}\}")
        
        def repl(match: re.Match) -> str:
            secret_key = match.group(1).upper()
            val = self.get(secret_key)
            return val if val is not None else match.group(0)

        return pattern.sub(repl, text)


# Global Vault instance
secret_vault = SecretVault()
