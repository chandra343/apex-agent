"""Lessons Store: Auto-capture error patterns into persistent DO/DON'T rules (Zeline Style)."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from apex.config import LESSONS_DB


class LessonsStore:
    """Manages persistent DO/DON'T lessons learned from tool errors and user corrections."""

    def __init__(self) -> None:
        self.db_path = LESSONS_DB
        self._init_db()

    def _init_db(self) -> None:
        LESSONS_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_pattern TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def record_lesson(self, trigger_pattern: str, rule_type: str, explanation: str) -> int:
        """Record a new DO or DONT guideline."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO lessons (trigger_pattern, rule_type, explanation, created_at)
                VALUES (?, ?, ?, ?)
            """, (trigger_pattern.lower().strip(), rule_type.upper().strip(), explanation.strip(), time.time()))
            conn.commit()
            return cur.lastrowid

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM lessons ORDER BY created_at DESC LIMIT 50")
            return [dict(r) for r in cur.fetchall()]

    def format_lessons_for_prompt(self, query: str = "") -> str:
        """Format matching lessons into a clean DO/DON'T list for prompt injection."""
        all_lessons = self.get_all_lessons()
        if not all_lessons:
            return ""

        do_rules = []
        dont_rules = []

        q_lower = query.lower()
        for item in all_lessons:
            trig = item["trigger_pattern"]
            # Check relevance
            if not query or trig in q_lower or any(word in q_lower for word in trig.split()):
                if item["rule_type"] == "DO":
                    do_rules.append(f"• DO: {item['explanation']} (when {trig})")
                else:
                    dont_rules.append(f"• DON'T: {item['explanation']} (when {trig})")

        if not do_rules and not dont_rules:
            return ""

        output = ["\n[Permanent Lessons & Operational Experience]:"]
        output.extend(do_rules[:5])
        output.extend(dont_rules[:5])
        return "\n".join(output)


# Global lessons store instance
lessons_store = LessonsStore()
