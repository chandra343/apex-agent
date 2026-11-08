"""Lobster Macro Shell Engine: Deterministic, token-saving tool pipelines."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple


class MacroPipeline:
    """Executes a series of tool steps deterministically without LLM roundtrips."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.steps: List[Dict[str, Any]] = []

    def add_step(
        self,
        tool_name: str,
        arguments_generator: Callable[[Dict[str, Any]], Dict[str, Any]],
        requires_approval: bool = False
    ) -> MacroPipeline:
        self.steps.append({
            "tool_name": tool_name,
            "arg_gen": arguments_generator,
            "requires_approval": requires_approval
        })
        return self

    def execute(
        self,
        initial_context: Dict[str, Any],
        tool_runner: Callable[[str, Dict[str, Any]], Tuple[bool, str]]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Run all steps sequentially, passing outputs into accumulated context."""
        ctx = dict(initial_context)
        logs: list[str] = [f"🚀 Starting Macro Pipeline: {self.name}"]

        for idx, step in enumerate(self.steps, 1):
            t_name = step["tool_name"]
            try:
                args = step["arg_gen"](ctx)
            except Exception as e:
                logs.append(f"❌ Step {idx} ({t_name}) argument generation failed: {e}")
                return False, "\n".join(logs), ctx

            logs.append(f"⚡ Step {idx}: Running {t_name}...")
            success, output = tool_runner(t_name, args)
            ctx[f"step_{idx}_output"] = output
            ctx[f"{t_name}_last_output"] = output

            if not success:
                logs.append(f"❌ Step {idx} ({t_name}) failed:\n{output[:300]}")
                return False, "\n".join(logs), ctx
            else:
                logs.append(f"✔ Step {idx} completed.")

        logs.append(f"🎉 Macro Pipeline '{self.name}' completed successfully.")
        return True, "\n".join(logs), ctx


class MacroRegistry:
    """Registry of pre-built and user-defined deterministic macros."""

    def __init__(self) -> None:
        self._macros: Dict[str, MacroPipeline] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        # 1. Project Git Hygiene Macro: Status -> Diff -> Branch
        git_macro = MacroPipeline("git_hygiene", "Quickly check git status and unstaged diffs")
        git_macro.add_step("git_status", lambda ctx: {})
        git_macro.add_step("git_diff", lambda ctx: {"staged": False})
        self.register(git_macro)

    def register(self, macro: MacroPipeline) -> None:
        self._macros[macro.name] = macro

    def get(self, name: str) -> Optional[MacroPipeline]:
        return self._macros.get(name)

    def list_macros(self) -> List[Dict[str, str]]:
        return [{"name": m.name, "description": m.description} for m in self._macros.values()]


# Global macro registry
macro_registry = MacroRegistry()
