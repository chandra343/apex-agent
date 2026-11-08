"""Lightweight Chrome DevTools Protocol (CDP) Client over WebSocket."""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, Optional, Tuple

try:
    import websockets
    import websockets.sync.client as ws_sync
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


class CDPClient:
    """Communicates with Lightpanda or any CDP-compatible browser over WebSocket."""

    def __init__(self, ws_url: str) -> None:
        self.ws_url = ws_url
        self._msg_id = 0
        self._conn: Optional[Any] = None
        self._lock = threading.Lock()

    def connect(self, timeout: float = 5.0) -> bool:
        if not HAS_WEBSOCKETS:
            return False
        try:
            self._conn = ws_sync.connect(self.ws_url, open_timeout=timeout)
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def send_command(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 15.0) -> Tuple[bool, Any]:
        """Send a CDP JSON-RPC command and await result."""
        if not self._conn:
            if not self.connect():
                return False, "Failed to connect to browser CDP endpoint."

        with self._lock:
            self._msg_id += 1
            cmd_id = self._msg_id

        req = {
            "id": cmd_id,
            "method": method,
            "params": params or {}
        }

        try:
            self._conn.send(json.dumps(req))
            start_t = time.time()
            while time.time() - start_t < timeout:
                raw_msg = self._conn.recv(timeout=timeout)
                parsed = json.loads(raw_msg)
                if parsed.get("id") == cmd_id:
                    if "error" in parsed:
                        return False, parsed["error"]
                    return True, parsed.get("result", {})
            return False, "CDP command timed out."
        except Exception as e:
            return False, f"CDP communication error: {e}"

    def navigate(self, url: str) -> Tuple[bool, str]:
        """Navigate to URL and wait for load."""
        ok, res = self.send_command("Page.navigate", {"url": url})
        if not ok:
            return False, str(res)
        return True, f"Navigated to {url}"

    def evaluate_js(self, expression: str) -> Tuple[bool, Any]:
        """Evaluate JavaScript inside the browser page."""
        ok, res = self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        })
        if not ok:
            return False, str(res)
        return True, res.get("result", {}).get("value")
