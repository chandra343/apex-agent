"""Dynamic Model Switcher with Cross-Provider Context Migration."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from apex.config import config


class ModelSwitcher:
    """Manages active models and migrates conversation context across providers."""

    def __init__(self) -> None:
        pass

    def get_available_models(self) -> List[Dict[str, str]]:
        """Return a structured list of all available models across configured providers."""
        models: List[Dict[str, str]] = []
        providers = config.get("providers", {})
        for p_name, p_data in providers.items():
            for m in p_data.get("models", []):
                models.append({
                    "id": m,
                    "provider": p_name,
                    "display": f"{m} ({p_name})"
                })
        return models

    def switch_model(self, new_model_id: str, session: Optional[Any] = None) -> str:
        """Switch active model for the given session or globally."""
        available = [m["id"].lower() for m in self.get_available_models()]
        target_id = new_model_id.strip()

        # Find best match
        matched_id = None
        for m in available:
            if target_id.lower() == m:
                matched_id = m
                break
            if target_id.lower() in m:
                matched_id = m

        if not matched_id:
            # If not in registered list, accept as custom model name
            matched_id = target_id

        if session is not None and hasattr(session, "active_model"):
            session.active_model = matched_id
        else:
            config.set("default_model", matched_id, auto_save=True)

        return matched_id

    def migrate_messages_for_target_model(
        self,
        messages: List[Dict[str, Any]],
        target_model: str
    ) -> List[Dict[str, Any]]:
        """Convert messages across formats (OpenAI <-> Anthropic) cleanly."""
        migrated: List[Dict[str, Any]] = []
        is_anthropic = "claude" in target_model.lower()

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Ensure content is always string or list of content blocks
            if isinstance(content, list) and not is_anthropic:
                # Collapse text blocks for OpenAI
                text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                content = "\n".join(text_parts) if text_parts else str(content)

            migrated_msg: Dict[str, Any] = {
                "role": role,
                "content": content
            }
            if "name" in msg:
                migrated_msg["name"] = msg["name"]
            if "tool_calls" in msg:
                migrated_msg["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                migrated_msg["tool_call_id"] = msg["tool_call_id"]

            migrated.append(migrated_msg)

        return migrated


# Global model switcher instance
model_switcher = ModelSwitcher()
