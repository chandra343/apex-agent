"""Progressive Disclosure Skills Manager (Hermes Style)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from apex.config import SKILLS_DIR, PKG_ROOT


class SkillManager:
    """Discovers and parses modular SKILL.md packages."""

    def __init__(self) -> None:
        self.user_skills_dir = SKILLS_DIR
        self.builtin_skills_dir = PKG_ROOT.parent / "skills"
        self._skills_cache: Dict[str, Dict[str, Any]] = {}
        self.reload_skills()

    def reload_skills(self) -> None:
        """Scan skills directories and parse frontmatters."""
        self._skills_cache.clear()
        dirs_to_scan = [self.builtin_skills_dir, self.user_skills_dir]

        for s_dir in dirs_to_scan:
            if not s_dir.exists():
                continue
            for skill_path in s_dir.glob("*/SKILL.md"):
                parsed = self._parse_skill_file(skill_path)
                if parsed:
                    self._skills_cache[parsed["name"]] = parsed

    def _parse_skill_file(self, skill_file: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()

            name = skill_file.parent.name
            desc = "Modular specialized capability"

            # Parse frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].splitlines():
                        if line.startswith("name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("description:"):
                            desc = line.split(":", 1)[1].strip()

            return {
                "name": name,
                "description": desc,
                "path": str(skill_file),
                "full_content": content
            }
        except Exception:
            return None

    def list_skills_for_prompt(self) -> str:
        """Format high-level skill list (name + description) for prompt progressive disclosure."""
        if not self._skills_cache:
            return ""

        lines = ["\n[Available Skills (Progressive Disclosure)]:\nAsk to activate when needed:"]
        for s in self._skills_cache.values():
            lines.append(f"• {s['name']}: {s['description']}")
        return "\n".join(lines)

    def get_skill_instructions(self, skill_name: str) -> Optional[str]:
        skill = self._skills_cache.get(skill_name)
        if skill:
            return skill["full_content"]
        return None

    def create_skill(self, name: str, description: str, instructions: str) -> str:
        """Create a new user skill package in ~/.apex/skills/<name>/SKILL.md."""
        target_dir = self.user_skills_dir / name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "SKILL.md"

        content = f"---\nname: {name}\ndescription: {description}\n---\n\n{instructions}\n"
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        self.reload_skills()
        return str(target_file)


# Global skill manager instance
skill_manager = SkillManager()
