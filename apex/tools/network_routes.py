"""Per-Request Network Routes and Proxy Manager (Zeline Style)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse
import requests
from apex.config import NETWORK_ROUTES_FILE


class NetworkRouteManager:
    """Manages HTTP(S) and SOCKS5 proxy routes on a per-domain/per-request basis."""

    def __init__(self) -> None:
        self._routes: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if NETWORK_ROUTES_FILE.exists():
            try:
                with open(NETWORK_ROUTES_FILE, "r", encoding="utf-8") as f:
                    self._routes = json.load(f)
            except Exception:
                self._routes = {}

    def _save(self) -> None:
        NETWORK_ROUTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(NETWORK_ROUTES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._routes, f, indent=2)
        except Exception:
            pass

    def add_route(self, domain_or_pattern: str, proxy_url: str) -> None:
        """Register a proxy route for a domain (e.g. 'blocked-site.com' -> 'socks5://127.0.0.1:9050')."""
        self._routes[domain_or_pattern.lower().strip()] = proxy_url.strip()
        self._save()

    def remove_route(self, domain_or_pattern: str) -> bool:
        key = domain_or_pattern.lower().strip()
        if key in self._routes:
            del self._routes[key]
            self._save()
            return True
        return False

    def get_proxy_for_url(self, target_url: str) -> Optional[Dict[str, str]]:
        """Resolve proxy for a given URL without affecting global process environment."""
        parsed = urlparse(target_url)
        host = (parsed.hostname or "").lower()

        for pattern, proxy in self._routes.items():
            if pattern == "*" or pattern == host or host.endswith(f".{pattern}"):
                return {"http": proxy, "https": proxy}
        return None

    def fetch(
        self,
        url: str,
        timeout: int = 20,
        headers: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, int]:
        """Fetch URL using matched route proxies."""
        proxies = self.get_proxy_for_url(url)
        hdrs = headers or {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        try:
            resp = requests.get(url, headers=hdrs, proxies=proxies, timeout=timeout)
            return resp.status_code == 200, resp.text, resp.status_code
        except Exception as e:
            return False, f"Network request error: {e}", 0


# Global route manager instance
route_manager = NetworkRouteManager()
