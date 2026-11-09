"""Autonomous Learning & Lessons Store Tools for Apex."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from apex.learning.lessons import lessons_store


def record_learned_lesson(
    trigger_pattern: str,
    rule_type: str,
    explanation: str
) -> str:
    """Record an operational DO or DONT lesson into Apex's permanent memory.

    Apex consults these lessons before executing future tasks to avoid repeating past mistakes.

    Args:
        trigger_pattern: Keyword, tool name, or error context that triggers this rule (e.g. 'git_commit', 'sql_query', 'nginx').
        rule_type: 'DO' (best practice to follow) or 'DONT' (pattern to avoid).
        explanation: Detailed rule and actionable guidance.

    Returns:
        Confirmation message with assigned lesson ID.
    """
    clean_trig = trigger_pattern.strip().lower()
    clean_type = rule_type.strip().upper()
    clean_exp = explanation.strip()

    if clean_type not in ["DO", "DONT"]:
        clean_type = "DONT" if "dont" in clean_type.lower() or "don't" in clean_type.lower() else "DO"

    if not clean_trig or not clean_exp:
        return "❌ Parameter `trigger_pattern` dan `explanation` wajib diisi."

    lesson_id = lessons_store.record_lesson(clean_trig, clean_type, clean_exp)
    icon = "💡" if clean_type == "DO" else "🛑"
    return f"{icon} **Pelajaran Tersimpan (#{lesson_id})**: `[{clean_type}]` pada trigger `{clean_trig}`: {clean_exp}"


def consult_learned_lessons(query: str = "") -> str:
    """Consult stored operational lessons and guidelines learned from previous executions.

    Args:
        query: Optional filter keyword (e.g. 'git', 'database', 'shell').

    Returns:
        Structured list of DO and DONT rules.
    """
    all_lessons = lessons_store.get_all_lessons()
    if not all_lessons:
        return "💡 Belum ada pelajaran operasional yang tercatat di basis data lessons."

    q_lower = query.strip().lower()
    matched = [l for l in all_lessons if not q_lower or q_lower in l["trigger_pattern"] or q_lower in l["explanation"].lower()]

    if not matched:
        return f"🔍 Tidak ditemukan pelajaran yang cocok dengan filter `{query}`."

    lines = [f"💡 **Daftar Pelajaran & Aturan Operasional ({len(matched)} Aturan)**:\n"]
    for idx, l in enumerate(matched[:20], 1):
        icon = "✅ [DO]" if l["rule_type"] == "DO" else "❌ [DONT]"
        trig = l["trigger_pattern"]
        exp = l["explanation"]
        lines.append(f"{idx}. **{icon}** `{trig}`: {exp}")

    return "\n".join(lines)
