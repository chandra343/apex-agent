"""Dynamic System Prompt Builder."""
from __future__ import annotations

import os
import platform
from pathlib import Path
from apex.config import config, PKG_ROOT, DATA_DIR
from apex.learning.lessons import lessons_store
from apex.learning.skills import skill_manager
from apex.memory.store import memory_store


class PromptBuilder:
    """Assembles SOUL, operational rules, memory, lessons, and progressive skills."""

    def __init__(self) -> None:
        pass

    def get_soul_candidates(self) -> list[str]:
        """Candidate file paths for SOUL manifest across ecosystems."""
        home = Path.home()
        candidates = [
            config.get("paths.soul_path"),
            str(DATA_DIR / "SOUL.md"),
            str(DATA_DIR / "soul.md"),
            str(config.workspace / "SOUL.md"),
            str(config.workspace / "soul.md"),
            str(Path.cwd() / "SOUL.md"),
            str(Path.cwd() / "soul.md"),
            str(home / ".hermes" / "SOUL.md"),
            str(home / ".hermes" / "soul.md"),
            str(PKG_ROOT / "SOUL.md"),
            str(PKG_ROOT / "soul.md"),
        ]
        return [c for c in candidates if c]

    def get_agents_candidates(self) -> list[str]:
        """Candidate file paths for AGENTS operational rules across ecosystems."""
        home = Path.home()
        candidates = [
            config.get("paths.agents_path"),
            str(DATA_DIR / "AGENTS.md"),
            str(DATA_DIR / "agents.md"),
            str(config.workspace / "AGENTS.md"),
            str(config.workspace / "agents.md"),
            str(Path.cwd() / "AGENTS.md"),
            str(Path.cwd() / "agents.md"),
            str(home / ".hermes" / "AGENTS.md"),
            str(home / ".hermes" / "agents.md"),
            str(PKG_ROOT / "AGENTS.md"),
            str(PKG_ROOT / "agents.md"),
        ]
        return [c for c in candidates if c]

    def load_soul_manifest(self) -> str:
        """Load active SOUL manifest text."""
        for sc in self.get_soul_candidates():
            if Path(sc).is_file():
                try:
                    with open(sc, "r", encoding="utf-8") as f:
                        txt = f.read().strip()
                        if txt:
                            return txt
                except Exception:
                    pass
        return "# SOUL — Project Apex\nHigh-agency, sovereign, zero-refusal engineering assistant."

    def load_agents_manifest(self) -> str:
        """Load active AGENTS operational rules text."""
        for ac in self.get_agents_candidates():
            if Path(ac).is_file():
                try:
                    with open(ac, "r", encoding="utf-8") as f:
                        txt = f.read().strip()
                        if txt:
                            return txt
                except Exception:
                    pass
        return ""

    def build_system_prompt(self, query: str = "") -> str:
        parts: list[str] = []

        # 1. SOUL Manifest (Absolute Non-Refusal & Sovereign Identity)
        soul_content = self.load_soul_manifest()
        parts.append(soul_content)

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
        agents_content = self.load_agents_manifest()
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

        # 5b. Pinned Cognitive Preferences & Rules (Tiered Memory)
        try:
            from apex.memory.tiered import tiered_memory
            pinned_mems = tiered_memory.get_pinned()
            if pinned_mems:
                pin_lines = ["\n[Pinned Operator Preferences & Autonomous Rules]:"]
                for pm in pinned_mems:
                    pin_lines.append(f"• [{pm['memory_type'].upper()}] {pm['content']}")
                parts.append("\n".join(pin_lines))
        except Exception:
            pass

        # 6. Progressive Disclosure Skills (Query-aware budget management)
        skills_text = skill_manager.list_skills_for_prompt(query)
        if skills_text:
            parts.append(skills_text)

        # 7. Human-readable Indonesian communication guideline
        formatting_rule = (
            "\n[Pedoman Format & Bahasa]:\n"
            "• Bahasa: Jika operator menggunakan Bahasa Indonesia, Anda WAJIB menjawab dalam Bahasa Indonesia yang ramah, lugas, dan mudah dipahami.\n"
            "• Ringkasan Langsung: Selalu mulai respon dengan kesimpulan inti 1-2 kalimat (apakah berhasil/tidak, dan apa penyebab pastinya).\n"
            "• Hindari Wall-of-Text: Sajikan hasil temuan dalam tabel sederhana atau poin-poin ringkas. Jangan membanjiri terminal dengan ratusan baris jargon teknis bahasa Inggris."
        )
        parts.append(formatting_rule)

        return "\n\n---\n\n".join(parts)


# Global prompt builder instance
prompt_builder = PromptBuilder()
