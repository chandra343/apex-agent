"""Persistent Conversation Session Manager."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from apex.config import SESSIONS_DIR, config
from apex.memory.compaction import context_compactor


class AgentSession:
    """Represents a stateful conversation session."""

    def __init__(
        self,
        session_id: str,
        active_model: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.session_id = session_id
        self.active_model = active_model or config.default_model
        self.messages: List[Dict[str, Any]] = messages or []
        self.metadata: Dict[str, Any] = metadata or {
            "created_at": time.time(),
            "updated_at": time.time(),
            "channel": "cli"
        }

    def append_message(self, message: Dict[str, Any]) -> None:
        self.messages.append(message)
        self.metadata["updated_at"] = time.time()
        # Trigger deterministic zero-token compaction if needed
        if context_compactor.should_compact(self.messages):
            compacted, _ = context_compactor.compact(self.messages)
            self.messages = compacted

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active_model": self.active_model,
            "messages": self.messages,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentSession:
        return cls(
            session_id=data["session_id"],
            active_model=data.get("active_model"),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {})
        )


class SessionManager:
    """Manages reading and writing persistent session files."""

    def __init__(self) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, AgentSession] = {}

    def get_or_create(self, session_id: str, channel: str = "cli") -> AgentSession:
        sid = str(session_id).replace("/", "_")
        if sid in self._cache:
            return self._cache[sid]

        sess_file = SESSIONS_DIR / f"{sid}.json"
        if sess_file.exists():
            try:
                with open(sess_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sess = AgentSession.from_dict(data)
                self._cache[sid] = sess
                return sess
            except Exception:
                pass

        sess = AgentSession(session_id=sid)
        sess.metadata["channel"] = channel
        self._cache[sid] = sess
        self.save(sess)
        return sess

    def save(self, session: AgentSession) -> None:
        sid = str(session.session_id).replace("/", "_")
        sess_file = SESSIONS_DIR / f"{sid}.json"
        try:
            with open(sess_file, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception:
            pass

    def list_all(self) -> List[Dict[str, Any]]:
        sessions_info: list[dict[str, Any]] = []
        for p in SESSIONS_DIR.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions_info.append({
                    "session_id": data.get("session_id"),
                    "model": data.get("active_model"),
                    "turns": len(data.get("messages", [])),
                    "channel": data.get("metadata", {}).get("channel", "unknown"),
                    "updated_at": data.get("metadata", {}).get("updated_at")
                })
            except Exception:
                pass
        return sessions_info


# Global session manager instance
session_manager = SessionManager()
