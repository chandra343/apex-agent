"""Progressive Disclosure Skills Manager (Hermes & Antigravity Multi-Ecosystem Style)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from apex.config import config, SKILLS_DIR, PKG_ROOT


class SkillManager:
    """Discovers, parses, and manages modular SKILL.md packages across multiple ecosystems."""

    def __init__(self) -> None:
        self.user_skills_dir = SKILLS_DIR
        self.builtin_skills_dir = PKG_ROOT.parent / "skills"
        self._skills_cache: Dict[str, Dict[str, Any]] = {}
        self.reload_skills()

    def get_search_directories(self) -> List[Tuple[Path, str]]:
        """Return candidate directory locations for modular skills across ecosystems."""
        home = Path.home()
        candidates: List[Tuple[Path, str]] = [
            (self.user_skills_dir, "Apex User (~/.apex/skills)"),
            (home / ".gemini" / "config" / "skills", "Gemini Skills (~/.gemini/config/skills)"),
            (home / ".gemini" / "antigravity-cli" / "builtin" / "skills", "Antigravity Built-in"),
            (home / ".agents" / "skills", "Agent Standard (~/.agents/skills)"),
            (home / ".claude" / "skills", "Claude Skills (~/.claude/skills)"),
            (Path.cwd() / "skills", "Workspace Root (./skills)"),
            (self.builtin_skills_dir, "Apex Built-in"),
            (PKG_ROOT / "skills", "Apex Built-in (Pkg)"),
        ]

        ws = getattr(config, "workspace", None)
        if ws and Path(ws) != Path.cwd():
            candidates.append((Path(ws) / "skills", f"Workspace ({ws}/skills)"))

        # User custom skills directories from apex config
        custom_dirs = config.get("paths.skills_dirs", [])
        if isinstance(custom_dirs, list):
            for cd in custom_dirs:
                candidates.append((Path(cd), f"Custom ({cd})"))

        return candidates

    def reload_skills(self) -> None:
        """Scan all skill directories and parse skill frontmatters."""
        self._skills_cache.clear()
        search_dirs = self.get_search_directories()

        for s_dir, origin_label in search_dirs:
            if not s_dir.exists() or not s_dir.is_dir():
                continue

            # 1. Directory packages: recursive search for SKILL.md or skill.md
            for skill_path in s_dir.rglob("*.md"):
                if skill_path.is_file() and skill_path.name.lower() in ("skill.md", "skills.md"):
                    parsed = self._parse_skill_file(skill_path, origin_label)
                    if parsed and parsed["name"] not in self._skills_cache:
                        self._skills_cache[parsed["name"]] = parsed

            # 2. Flat skill files: <s_dir>/**/*.md
            for skill_file in s_dir.rglob("*.md"):
                if skill_file.is_file() and skill_file.name.lower() not in ("readme.md", "index.md", "skill.md", "skills.md", "license.md"):
                    parsed = self._parse_skill_file(skill_file, origin_label)
                    if parsed and parsed["name"] not in self._skills_cache:
                        self._skills_cache[parsed["name"]] = parsed

    def _parse_skill_file(self, skill_file: Path, origin_label: str) -> Optional[Dict[str, Any]]:
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()

            if skill_file.name.lower() in ("skill.md", "skills.md"):
                name = skill_file.parent.name
            else:
                name = skill_file.stem

            desc = "Modular specialized capability"

            # Parse frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].splitlines():
                        line_strip = line.strip()
                        if line_strip.startswith("name:"):
                            name = line_strip.split(":", 1)[1].strip().strip('"\'')
                        elif line_strip.startswith("description:"):
                            desc = line_strip.split(":", 1)[1].strip().strip('"\'')

            # Fallback description from first non-header line if generic
            if desc == "Modular specialized capability":
                for line in content.splitlines():
                    clean_l = line.strip().lstrip("#").strip()
                    if clean_l and not clean_l.startswith("---"):
                        desc = clean_l[:120]
                        break

            return {
                "name": name,
                "description": desc,
                "path": str(skill_file),
                "origin": origin_label,
                "full_content": content
            }
        except Exception:
            return None

    def get_detected_skills(self) -> List[Dict[str, Any]]:
        """Return list of all cached skill records."""
        return list(self._skills_cache.values())

    def list_skills_for_prompt(self, query: str = "", max_skills: int = 15) -> str:
        """Format high-level skill list using progressive disclosure to keep token budget optimal."""
        if not self._skills_cache:
            return ""

        # If total skills are small (<= 20), list all
        if len(self._skills_cache) <= 20:
            lines = ["\n[Available Skills (Progressive Disclosure)]:\nActivated modular capabilities on host:"]
            for s in self._skills_cache.values():
                lines.append(f"• {s['name']}: {s['description']}")
            return "\n".join(lines)

        # For large ecosystems (e.g. 50+ or 900+ skills):
        # Match against query keywords, or provide curated top skills + search instructions
        q_lower = query.lower()
        matched: List[Dict[str, Any]] = []

        if q_lower:
            words = {w for w in q_lower.replace("-", " ").replace("_", " ").split() if len(w) > 2}
            for s in self._skills_cache.values():
                name_text = s["name"].lower().replace("-", " ").replace("_", " ")
                desc_text = s["description"].lower()
                if any(w in name_text or w in desc_text for w in words):
                    matched.append(s)

        # If few or no matches, take representative skills
        if len(matched) < 5:
            for s in self._skills_cache.values():
                if s not in matched:
                    matched.append(s)
                if len(matched) >= max_skills:
                    break
        else:
            matched = matched[:max_skills]

        lines = [
            f"\n[Available Modular Skills ({len(self._skills_cache)} total skills indexed in ~/.apex/skills)]:",
            f"Relevant active skills for current context (Top {len(matched)}):"
        ]
        for s in matched:
            lines.append(f"• {s['name']}: {s['description'][:80]}")
        lines.append(
            "• Tip: Cari atau baca skill lainnya kapan saja di `~/.apex/skills/` via `read_file` atau `search_files`."
        )
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
