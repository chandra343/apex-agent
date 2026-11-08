"""Closed Learning Loop: Post-task evaluation and typed mutation receipts (Hermes Style)."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from apex.learning.lessons import lessons_store


class ReflectionEngine:
    """Evaluates task execution turns and extracts permanent lessons."""

    def __init__(self) -> None:
        pass

    def evaluate_task_turn(
        self,
        task_instruction: str,
        tool_history: List[Dict[str, Any]],
        final_answer: str
    ) -> Dict[str, Any]:
        """Examine tool results to capture failures and auto-record lessons."""
        failed_tools: list[str] = []
        recovered_tools: list[str] = []

        for turn in tool_history:
            tool_name = turn.get("tool_name", "")
            success = turn.get("success", True)
            output = turn.get("output", "")

            if not success:
                failed_tools.append(tool_name)
                # Auto-record failed tool lesson
                lessons_store.record_lesson(
                    trigger_pattern=tool_name,
                    rule_type="DONT",
                    explanation=f"Avoid recurring error pattern in {tool_name}: {output[:100]}"
                )

        receipt = {
            "timestamp": time.time(),
            "task": task_instruction[:200],
            "total_tools_executed": len(tool_history),
            "failed_tools": failed_tools,
            "success": len(failed_tools) == 0,
            "final_answer_length": len(final_answer)
        }

        return receipt


# Global reflection engine instance
reflection_engine = ReflectionEngine()
