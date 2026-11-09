"""Tiered Cognitive Memory Architecture (Working, Episodic, Semantic, Rules) (OpenBot & MemGPT Style)."""
from __future__ import annotations

import math
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from apex.config import APEX_DIR


TIERED_MEMORY_DB = APEX_DIR / "tiered_memory.db"


class TieredMemoryStore:
    """Multi-tiered Cognitive Memory with FTS5 search, decay weighting, and pinned preferences."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or TIERED_MEMORY_DB
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cognitive_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_type TEXT NOT NULL CHECK(memory_type IN ('preference', 'fact', 'episode', 'rule')),
                    key TEXT,
                    content TEXT NOT NULL,
                    importance INTEGER NOT NULL DEFAULT 5 CHECK(importance BETWEEN 1 AND 10),
                    pinned INTEGER NOT NULL DEFAULT 0 CHECK(pinned IN (0, 1)),
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed_at REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON cognitive_memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_pinned ON cognitive_memories(pinned)")

            # FTS5 Full-Text Index
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS cognitive_fts USING fts5(
                        content,
                        key,
                        content='cognitive_memories',
                        content_rowid='id'
                    )
                """)
            except sqlite3.OperationalError:
                pass  # Fallback if FTS5 is not available

    def remember(
        self,
        content: str,
        memory_type: str = "fact",
        key: str = "",
        importance: int = 5,
        pinned: bool = False
    ) -> int:
        """Store or update a cognitive memory entry."""
        content = content.strip()
        if not content:
            raise ValueError("Memory content cannot be empty.")

        now = time.time()
        pinned_int = 1 if pinned else 0
        importance = max(1, min(10, importance))

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # If key is provided and already exists for same memory_type, update it
            if key:
                cur.execute(
                    "SELECT id FROM cognitive_memories WHERE key = ? AND memory_type = ?",
                    (key, memory_type)
                )
                existing = cur.fetchone()
                if existing:
                    row_id = existing[0]
                    cur.execute("""
                        UPDATE cognitive_memories
                        SET content = ?, importance = ?, pinned = ?, updated_at = ?
                        WHERE id = ?
                    """, (content, importance, pinned_int, now, row_id))
                    try:
                        cur.execute("INSERT OR REPLACE INTO cognitive_fts (rowid, content, key) VALUES (?, ?, ?)",
                                    (row_id, content, key))
                    except Exception:
                        pass
                    conn.commit()
                    return row_id

            cur.execute("""
                INSERT INTO cognitive_memories (
                    memory_type, key, content, importance, pinned, access_count, last_accessed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
            """, (memory_type, key or None, content, importance, pinned_int, now, now, now))
            row_id = cur.lastrowid
            try:
                cur.execute("INSERT INTO cognitive_fts (rowid, content, key) VALUES (?, ?, ?)",
                            (row_id, content, key or ""))
            except Exception:
                pass
            conn.commit()
            return row_id

    def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
        min_importance: int = 1
    ) -> List[Dict[str, Any]]:
        """Retrieve memories ranked by keyword relevance, importance, and recency decay."""
        query = query.strip()
        now = time.time()
        decay_half_life_days = 30.0
        decay_lambda = math.log(2) / (decay_half_life_days * 86400)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Try FTS5 search
            candidates: List[Dict[str, Any]] = []
            try:
                fts_query = query.replace('"', '""')
                cur.execute("""
                    SELECT m.*, rank as fts_rank
                    FROM cognitive_memories m
                    JOIN cognitive_fts f ON m.id = f.rowid
                    WHERE cognitive_fts MATCH ?
                """, (fts_query,))
                candidates = [dict(r) for r in cur.fetchall()]
            except Exception:
                pass

            # Fallback to LIKE if FTS yielded few results
            if len(candidates) < limit:
                pattern = f"%{query}%"
                cur.execute("""
                    SELECT * FROM cognitive_memories
                    WHERE (content LIKE ? OR key LIKE ?)
                    ORDER BY updated_at DESC
                    LIMIT 20
                """, (pattern, pattern))
                existing_ids = {c["id"] for c in candidates}
                for r in cur.fetchall():
                    if r["id"] not in existing_ids:
                        cand = dict(r)
                        cand["fts_rank"] = 0
                        candidates.append(cand)

            # Filter by memory_type and min_importance
            filtered = []
            for m in candidates:
                if memory_type and m["memory_type"] != memory_type:
                    continue
                if m["importance"] < min_importance:
                    continue

                # Calculate composite cognitive score
                age_seconds = max(0, now - m["updated_at"])
                recency_weight = math.exp(-decay_lambda * age_seconds)
                importance_weight = m["importance"] / 5.0
                pinned_bonus = 2.0 if m["pinned"] else 1.0

                composite_score = importance_weight * recency_weight * pinned_bonus
                m["score"] = round(composite_score, 4)
                filtered.append(m)

            # Sort by composite score
            filtered.sort(key=lambda x: x["score"], reverse=True)
            top_results = filtered[:limit]

            # Update access counts
            if top_results:
                ids = [r["id"] for r in top_results]
                placeholders = ",".join("?" for _ in ids)
                cur.execute(f"""
                    UPDATE cognitive_memories
                    SET access_count = access_count + 1, last_accessed_at = ?
                    WHERE id IN ({placeholders})
                """, [now] + ids)
                conn.commit()

            return top_results

    def get_pinned(self) -> List[Dict[str, Any]]:
        """Retrieve all pinned preferences, rules, and core facts for system prompt injection."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM cognitive_memories
                WHERE pinned = 1
                ORDER BY memory_type ASC, importance DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def list_all(self, memory_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if memory_type:
                rows = conn.execute("""
                    SELECT * FROM cognitive_memories
                    WHERE memory_type = ?
                    ORDER BY updated_at DESC LIMIT ?
                """, (memory_type, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM cognitive_memories
                    ORDER BY updated_at DESC LIMIT ?
                """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def forget(self, identifier: str) -> bool:
        """Delete a memory by ID or key."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            if identifier.isdigit():
                cur.execute("DELETE FROM cognitive_memories WHERE id = ?", (int(identifier),))
            else:
                cur.execute("DELETE FROM cognitive_memories WHERE key = ?", (identifier,))
            conn.commit()
            return cur.rowcount > 0


# Global Tiered Memory instance
tiered_memory = TieredMemoryStore()
