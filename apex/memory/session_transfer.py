"""Session Transfer, Forking & Export/Import Engine (Zeline Style)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from apex.memory.sessions import session_manager, AgentSession


class SessionTransfer:
    """Provides cross-channel session transfer, branching (--fork), and JSON export/import."""

    def __init__(self) -> None:
        pass

    def transfer(self, source_id: str, target_id: str, target_channel: str = "telegram") -> Tuple[bool, str]:
        """Move or copy an active session to another channel or chat ID."""
        src_sess = session_manager.get_or_create(source_id)
        if not src_sess.messages:
            return False, f"Source session '{source_id}' is empty or does not exist."

        tgt_sess = session_manager.get_or_create(target_id, channel=target_channel)
        tgt_sess.messages = [dict(m) for m in src_sess.messages]
        tgt_sess.active_model = src_sess.active_model
        tgt_sess.metadata["channel"] = target_channel
        tgt_sess.metadata["transferred_from"] = source_id
        tgt_sess.metadata["transferred_at"] = time.time()

        session_manager.save(tgt_sess)
        return True, f"Session successfully transferred from '{source_id}' to '{target_id}' ({target_channel})"

    def fork(self, source_id: str, fork_suffix: Optional[str] = None) -> Tuple[bool, str, str]:
        """Branch an exploration into a new session ID without altering original history."""
        src_sess = session_manager.get_or_create(source_id)
        suffix = fork_suffix or f"fork_{int(time.time())}"
        new_id = f"{source_id}_{suffix}"

        forked_sess = AgentSession(
            session_id=new_id,
            active_model=src_sess.active_model,
            messages=[dict(m) for m in src_sess.messages],
            metadata={
                "forked_from": source_id,
                "created_at": time.time(),
                "channel": src_sess.metadata.get("channel", "cli")
            }
        )
        session_manager.save(forked_sess)
        return True, f"Session forked to: {new_id}", new_id

    def export_to_json(self, session_id: str, output_path: str) -> Tuple[bool, str]:
        """Export session to a shareable JSON file (sanitizing system prompts)."""
        sess = session_manager.get_or_create(session_id)
        out_p = Path(output_path).expanduser().resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize: drop system prompt so imported session builds cleanly from user config
        sanitized_messages = [m for m in sess.messages if m.get("role") != "system"]

        export_data = {
            "version": "1.0.0",
            "session_id": sess.session_id,
            "active_model": sess.active_model,
            "exported_at": time.time(),
            "messages": sanitized_messages
        }

        try:
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            return True, f"Exported {len(sanitized_messages)} messages to {out_p}"
        except Exception as e:
            return False, f"Failed to export session: {e}"

    def import_from_json(self, input_path: str, target_id: str) -> Tuple[bool, str]:
        """Import a conversation JSON dump into a session."""
        inp = Path(input_path).expanduser().resolve()
        if not inp.exists() or not inp.is_file():
            return False, f"Import file not found: {inp}"

        try:
            with open(inp, "r", encoding="utf-8") as f:
                data = json.load(f)

            messages = data.get("messages", [])
            # Drop imported system messages for safety
            safe_messages = [m for m in messages if m.get("role") != "system"]

            sess = session_manager.get_or_create(target_id)
            sess.messages = safe_messages
            if "active_model" in data:
                sess.active_model = data["active_model"]

            session_manager.save(sess)
            return True, f"Imported {len(safe_messages)} messages into session '{target_id}'"
        except Exception as e:
            return False, f"Failed to import session: {e}"


# Global session transfer instance
session_transfer = SessionTransfer()
