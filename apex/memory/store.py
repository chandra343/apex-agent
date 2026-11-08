"""SQLite FTS5 Transactional Memory Store (Hermes & Zeline Style)."""
from __future__ import annotations

import sqlite3
import time
from typing import Any, Dict, List, Optional
from apex.config import MEMORY_DB


class MemoryStore:
    """Manages persistent long-term memory using SQLite with FTS5 full-text indexing."""

    def __init__(self) -> None:
        self.db_path = MEMORY_DB
        self._init_db()

    def _init_db(self) -> None:
        MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    created_at REAL NOT NULL
                )
            """)
            # FTS5 virtual table for lightning-fast search
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                        content,
                        tags,
                        content='memory_entries',
                        content_rowid='id'
                    )
                """)
            except sqlite3.OperationalError:
                pass  # Fallback if FTS5 is not compiled in sqlite3

    def store(self, content: str, category: str = "general", tags: str = "") -> int:
        """Store a new fact or lesson in long-term memory."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO memory_entries (category, content, tags, created_at) VALUES (?, ?, ?, ?)",
                (category, content.strip(), tags.strip(), time.time())
            )
            row_id = cur.lastrowid
            try:
                cur.execute(
                    "INSERT INTO memory_fts (rowid, content, tags) VALUES (?, ?, ?)",
                    (row_id, content.strip(), tags.strip())
                )
            except Exception:
                pass
            conn.commit()
            return row_id

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory entries using FTS5 match or LIKE fallback."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Try FTS5 first
            try:
                cur.execute("""
                    SELECT e.id, e.category, e.content, e.tags, e.created_at
                    FROM memory_entries e
                    JOIN memory_fts f ON e.id = f.rowid
                    WHERE memory_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))
                rows = cur.fetchall()
                if rows:
                    return [dict(r) for r in rows]
            except Exception:
                pass

            # Fallback to standard LIKE query
            pattern = f"%{query}%"
            cur.execute("""
                SELECT id, category, content, tags, created_at
                FROM memory_entries
                WHERE content LIKE ? OR tags LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (pattern, pattern, limit))
            return [dict(r) for r in cur.fetchall()]

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, category, content, tags, created_at
                FROM memory_entries
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]


# Global memory store instance
memory_store = MemoryStore()
