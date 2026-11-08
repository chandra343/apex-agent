"""Multi-Account Pooling & Round-Robin Key Rotation Engine."""
from __future__ import annotations

import time
from typing import Dict, List, Optional


class KeyPool:
    """Manages multi-key rotation and cooldown tracking per provider."""

    def __init__(self, cooldown_seconds: int = 60) -> None:
        self.cooldown_seconds = cooldown_seconds
        # provider -> list of keys
        self._keys: Dict[str, List[str]] = {}
        # key -> cooldown_until_timestamp
        self._cooldowns: Dict[str, float] = {}
        # provider -> current round-robin index
        self._indices: Dict[str, int] = {}

    def set_keys(self, provider: str, keys: List[str] | str) -> None:
        """Register one or more keys for a provider."""
        if isinstance(keys, str):
            key_list = [k.strip() for k in keys.split(",") if k.strip()]
        else:
            key_list = [k.strip() for k in keys if k.strip()]
        
        self._keys[provider] = key_list
        if provider not in self._indices:
            self._indices[provider] = 0

    def get_key(self, provider: str) -> Optional[str]:
        """Retrieve the next ready API key using round-robin rotation."""
        keys = self._keys.get(provider, [])
        if not keys:
            return None

        now = time.time()
        start_idx = self._indices.get(provider, 0)
        total = len(keys)

        for i in range(total):
            idx = (start_idx + i) % total
            candidate = keys[idx]
            cooldown_until = self._cooldowns.get(candidate, 0.0)
            if now >= cooldown_until:
                # Key is ready! Advance index for next call
                self._indices[provider] = (idx + 1) % total
                return candidate

        # All keys are in cooldown; return the one expiring soonest
        soonest_key = min(keys, key=lambda k: self._cooldowns.get(k, 0.0))
        return soonest_key

    def mark_rate_limited(self, key: str, custom_cooldown: Optional[float] = None) -> None:
        """Put a key into cooldown after receiving HTTP 429."""
        cd = custom_cooldown if custom_cooldown is not None else self.cooldown_seconds
        self._cooldowns[key] = time.time() + cd

    def is_cooling_down(self, key: str) -> bool:
        """Check if an API key is currently in cooldown."""
        return time.time() < self._cooldowns.get(key, 0.0)

    def remaining_cooldown(self, key: str) -> float:
        """Return remaining seconds in cooldown (0 if ready)."""
        rem = self._cooldowns.get(key, 0.0) - time.time()
        return max(0.0, rem)


# Global singleton instance
key_pool = KeyPool()
