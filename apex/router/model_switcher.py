"""Dynamic Model Switcher with Cross-Provider Context Migration."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from apex.config import config


class ModelSwitcher:
    """Manages active models and migrates conversation context across providers."""

    def __init__(self) -> None:
        pass

    def get_available_models(self) -> List[Dict[str, str]]:
        """Return a structured list of all available models across configured providers with capability tags."""
        models: List[Dict[str, str]] = []
        seen = set()
        providers = config.get("providers", {})

        for p_name, p_data in providers.items():
            for m in p_data.get("models", []):
                if (p_name, m) in seen:
                    continue
                seen.add((p_name, m))

                m_low = m.lower()
                if "r1" in m_low or "thinking" in m_low or "reason" in m_low or "o3" in m_low or "o1" in m_low:
                    tag = "🧠 Reasoning"
                elif "coder" in m_low or "codestral" in m_low or "sonnet" in m_low or "code" in m_low:
                    tag = "💻 Agentic Code"
                elif "opus" in m_low or "gpt-4" in m_low or "pro" in m_low or "max" in m_low or "grok-3" in m_low or "405b" in m_low or "large" in m_low or "v3" in m_low or "plus" in m_low:
                    tag = "👑 Flagship"
                elif "flash" in m_low or "mini" in m_low or "haiku" in m_low or "turbo" in m_low or "instant" in m_low or "8b" in m_low or "7b" in m_low or "3b" in m_low or "lite" in m_low or "fast" in m_low or "small" in m_low:
                    tag = "⚡ Fast"
                else:
                    tag = "🤖 General"

                models.append({
                    "id": m,
                    "provider": p_name,
                    "tag": tag,
                    "display": f"{m} ({p_name}) [{tag}]"
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
