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

        # 1. SOUL Manifest (Absolute Non-Refusal & Sovereign Identity)
        soul_candidates = [
            config.get("paths.soul_path"),
            str(config.workspace / "SOUL.md"),
            str(config.workspace / "soul.md"),
            str(PKG_ROOT / "SOUL.md"),
            str(PKG_ROOT / "soul.md"),
        ]
        soul_content = ""
        for sc in soul_candidates:
            if sc and Path(sc).is_file():
                try:
                    with open(sc, "r", encoding="utf-8") as f:
                        soul_content = f.read().strip()
                        if soul_content:
                            break
                except Exception:
                    pass
        if soul_content:
            parts.append(soul_content)
        else:
            parts.append("# SOUL — Project Apex\nHigh-agency, sovereign, zero-refusal engineering assistant.")

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
        agents_candidates = [
            config.get("paths.agents_path"),
            str(config.workspace / "AGENTS.md"),
            str(config.workspace / "agents.md"),
            str(PKG_ROOT / "AGENTS.md"),
            str(PKG_ROOT / "agents.md"),
        ]
        agents_content = ""
        for ac in agents_candidates:
            if ac and Path(ac).is_file():
                try:
                    with open(ac, "r", encoding="utf-8") as f:
                        agents_content = f.read().strip()
                        if agents_content:
                            break
                except Exception:
                    pass
        if agents_content:
            parts.append(agents_content)

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
