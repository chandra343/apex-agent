"""Zero-Token Context Compaction Engine (Zeline Style)."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


class ContextCompactor:
    """Compresses message history deterministically without spending LLM tokens."""

    def __init__(self, max_turns: int = 30, max_chars_per_tool_result: int = 1500) -> None:
        self.max_turns = max_turns
        self.max_chars_per_tool_result = max_chars_per_tool_result

    def should_compact(self, messages: List[Dict[str, Any]]) -> bool:
        """Check if message count exceeds threshold."""
        return len(messages) > self.max_turns

    def compact(self, messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Compact conversation history deterministically.

        Returns:
            Tuple[compacted_messages, tokens_saved_estimate]
        """
        if not messages:
            return [], 0

        original_chars = sum(len(str(m.get("content", ""))) for m in messages)
        compacted: List[Dict[str, Any]] = []

        # Keep system prompt if present
        start_idx = 0
        if messages and messages[0].get("role") == "system":
            compacted.append(dict(messages[0]))
            start_idx = 1

        # Determine partition: keep the most recent N turns intact
        recent_window = 10
        total_remaining = len(messages) - start_idx

        if total_remaining <= recent_window:
            older_messages = []
            recent_messages = messages[start_idx:]
        else:
            split_point = len(messages) - recent_window
            older_messages = messages[start_idx:split_point]
            recent_messages = messages[split_point:]

        # Compact older messages
        older_summary_parts: list[str] = []
        for msg in older_messages:
            role = msg.get("role", "")
            content = str(msg.get("content", "")).strip()

            if role == "user":
                older_summary_parts.append(f"• User requested: {content[:200]}")
            elif role == "assistant":
                # If assistant made tool calls
                if "tool_calls" in msg:
                    tools_used = [tc.get("function", {}).get("name", "tool") for tc in msg.get("tool_calls", [])]
                    older_summary_parts.append(f"• Assistant executed tools: {', '.join(tools_used)}")
                elif content:
                    older_summary_parts.append(f"• Assistant stated: {content[:150]}")
            elif role == "tool":
                tool_name = msg.get("name", "tool")
                older_summary_parts.append(f"• Result ({tool_name}): {content[:100]}... [truncated]")

        if older_summary_parts:
            summary_message = {
                "role": "user",
                "content": (
                    "[Deterministic Context Compaction Summary of earlier conversation]:\n"
                    + "\n".join(older_summary_parts[:25])
                )
            }
            assistant_ack = {
                "role": "assistant",
                "content": "Understood. I retain the summarized context of our earlier progress."
            }
            compacted.append(summary_message)
            compacted.append(assistant_ack)

        # Append recent turns with tool result pruning if oversized
        for msg in recent_messages:
            msg_copy = dict(msg)
            if msg_copy.get("role") == "tool":
                content = str(msg_copy.get("content", ""))
                if len(content) > self.max_chars_per_tool_result:
                    msg_copy["content"] = content[:self.max_chars_per_tool_result] + "\n... [pruned for context budget]"
            compacted.append(msg_copy)

        new_chars = sum(len(str(m.get("content", ""))) for m in compacted)
        saved_chars = max(0, original_chars - new_chars)
        estimated_tokens_saved = saved_chars // 4

        return compacted, estimated_tokens_saved


# Global context compactor
context_compactor = ContextCompactor()
