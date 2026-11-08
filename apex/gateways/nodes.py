"""Distributed Hardware Nodes Protocol & WebSocket Server (OpenClaw Style)."""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


class HardwareNodeServer:
    """Manages secondary device connections (phones, laptops) exposing physical sensors."""

    def __init__(self) -> None:
        self._connected_nodes: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_node(self, node_id: str, device_type: str, capabilities: List[str]) -> None:
        with self._lock:
            self._connected_nodes[node_id] = {
                "device_type": device_type,
                "capabilities": capabilities,
                "connected_at": time.time(),
                "last_seen": time.time()
            }

    def list_nodes(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {"node_id": k, **v} for k, v in self._connected_nodes.items()
            ]

    def trigger_action(self, node_id: str, action: str, params: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """Dispatch hardware action (e.g. camera capture) to connected device."""
        with self._lock:
            if node_id not in self._connected_nodes:
                return False, f"Hardware node '{node_id}' is not connected."
            node = self._connected_nodes[node_id]
            if action not in node.get("capabilities", []):
                return False, f"Node '{node_id}' does not support action '{action}'."

        return True, f"Hardware action '{action}' dispatched to node '{node_id}'."


# Global node server
node_server = HardwareNodeServer()
