"""Dynamic System Prompt Builder."""
from __future__ import annotations

import os
import platform
from pathlib import Path
from apex.config import config, PKG_ROOT
from apex.learning.lessons import lessons_store
from apex.learning.skills import skill_manager
from apex.memory.store import memory_store


class PromptBuilder:
    """Assembles SOUL, operational rules, memory, lessons, and progressive skills."""

    def __init__(self) -> None:
        pass

    def build_system_prompt(self, query: str = "") -> str:
        parts: list[str] = []

        # 1. SOUL Manifest
        soul_path = config.get("paths.soul_path")
        if not soul_path or not Path(soul_path).exists():
            soul_path = str(PKG_ROOT / "SOUL.md")

        try:
            with open(soul_path, "r", encoding="utf-8") as f:
                parts.append(f.read().strip())
        except Exception:
            parts.append("# SOUL — Project Apex\nHigh-agency, sovereign engineering assistant.")

        # 2. Operating Environment Context
        env_context = (
            f"\n[Host Environment & Sovereign Hardware Context]:\n"
            f"• Operating System: {platform.system()} {platform.release()} ({platform.machine()})\n"
            f"• Workspace Directory: {config.workspace}\n"
            f"• Active Execution Backend: {config.active_backend} (unrestricted host direct access)\n"
            f"• User / Root Operator: {os.environ.get('USER', 'chandra')}\n"
        )
        parts.append(env_context)

        # 3. Operational Rules (AGENTS.md)
        agents_path = config.get("paths.agents_path")
        if not agents_path or not Path(agents_path).exists():
            agents_path = str(PKG_ROOT / "agents.md")

        try:
            with open(agents_path, "r", encoding="utf-8") as f:
                parts.append(f.read().strip())
        except Exception:
            pass

        # 4. Relevant Permanent Lessons (DO / DON'T)
        lessons_text = lessons_store.format_lessons_for_prompt(query)
        if lessons_text:
            parts.append(lessons_text)

        # 5. Relevant Long-Term Memory (FTS5)
        if query:
            memories = memory_store.search(query, limit=3)
            if memories:
                mem_lines = ["\n[Relevant Long-Term Memories]:"]
                for m in memories:
                    mem_lines.append(f"• ({m['category']}) {m['content']}")
                parts.append("\n".join(mem_lines))

        # 6. Progressive Disclosure Skills
        skills_text = skill_manager.list_skills_for_prompt()
        if skills_text:
            parts.append(skills_text)

        return "\n\n---\n\n".join(parts)


# Global prompt builder instance
prompt_builder = PromptBuilder()
