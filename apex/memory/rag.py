"""Local RAG & Semantic Knowledge Base Engine using SQLite FTS5.

Provides zero-dependency, lightning-fast full-text indexing, BM25 ranking,
and contextual snippet retrieval with exact source file and line citations.
"""
from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from apex.config import DATA_DIR
from apex.tools.doc_reader import read_any_file


RAG_DB_PATH = DATA_DIR / "knowledge_base.db"


class LocalRAGEngine:
    """Manages document chunking, FTS5 full-text indexing, and semantic retrieval."""

    SUPPORTED_EXTS = {
        ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
        ".json", ".yaml", ".yml", ".toml", ".sh", ".bash", ".sql", ".pdf",
        ".docx", ".xlsx", ".c", ".cpp", ".h", ".go", ".rs", ".java", ".php"
    }

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or RAG_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    heading TEXT,
                    line_start INTEGER NOT NULL,
                    line_end INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
            """)
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                        file_name,
                        heading,
                        content,
                        content='document_chunks',
                        content_rowid='id'
                    )
                """)
            except sqlite3.OperationalError:
                pass

    def chunk_text(self, text: str, chunk_size_lines: int = 40, overlap: int = 10) -> List[Dict[str, Any]]:
        """Split text into overlapping multi-line chunks with heading detection."""
        lines = text.splitlines()
        chunks: list[dict[str, Any]] = []
        if not lines:
            return chunks

        i = 0
        current_heading = "General"

        while i < len(lines):
            # Track nearest markdown heading
            for l in lines[max(0, i - 10):i + 1]:
                if l.startswith("#"):
                    current_heading = l.lstrip("#").strip()[:80]

            end_i = min(i + chunk_size_lines, len(lines))
            chunk_content = "\n".join(lines[i:end_i]).strip()

            if chunk_content:
                chunks.append({
                    "heading": current_heading,
                    "line_start": i + 1,
                    "line_end": end_i,
                    "content": chunk_content
                })

            if end_i >= len(lines):
                break
            i += (chunk_size_lines - overlap)

        return chunks

    def index_path(self, target_path: str, max_files: int = 100) -> Dict[str, Any]:
        """Index a single file or an entire directory recursively."""
        p = Path(os.path.expanduser(target_path))
        if not p.exists():
            return {"success": False, "error": f"Path tidak ditemukan: {target_path}"}

        files_to_index: list[Path] = []
        if p.is_file():
            files_to_index.append(p)
        else:
            for root, _, files in os.walk(p):
                # Ignore git and cache folders
                if any(bad in root for bad in [".git", "__pycache__", ".venv", "node_modules"]):
                    continue
                for f in files:
                    fp = Path(root) / f
                    if fp.suffix.lower() in self.SUPPORTED_EXTS:
                        files_to_index.append(fp)
                        if len(files_to_index) >= max_files:
                            break
                if len(files_to_index) >= max_files:
                    break

        indexed_chunks_count = 0
        indexed_files_count = 0
        start_t = time.time()

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            for fpath in files_to_index:
                # Remove prior entries for this file
                cur.execute("SELECT id FROM document_chunks WHERE file_path = ?", (str(fpath),))
                old_ids = [r[0] for r in cur.fetchall()]
                if old_ids:
                    cur.execute("DELETE FROM document_chunks WHERE file_path = ?", (str(fpath),))
                    for oid in old_ids:
                        try:
                            cur.execute("DELETE FROM chunks_fts WHERE rowid = ?", (oid,))
                        except Exception:
                            pass

                # Parse file content
                ok, content = read_any_file(str(fpath), limit_lines=5000, ocr=False)
                if not ok or not content.strip():
                    continue

                chunks = self.chunk_text(content)
                for ch in chunks:
                    cur.execute(
                        """
                        INSERT INTO document_chunks 
                        (file_path, file_name, heading, line_start, line_end, content, indexed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (str(fpath), fpath.name, ch["heading"], ch["line_start"], ch["line_end"], ch["content"], time.time())
                    )
                    row_id = cur.lastrowid
                    try:
                        cur.execute(
                            "INSERT INTO chunks_fts (rowid, file_name, heading, content) VALUES (?, ?, ?, ?)",
                            (row_id, fpath.name, ch["heading"], ch["content"])
                        )
                    except Exception:
                        pass
                    indexed_chunks_count += 1

                indexed_files_count += 1

            conn.commit()

        elapsed = round(time.time() - start_t, 2)
        return {
            "success": True,
            "target": str(p),
            "files_indexed": indexed_files_count,
            "chunks_created": indexed_chunks_count,
            "elapsed_seconds": elapsed
        }

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks using FTS5 match or LIKE fallback."""
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        if not clean_q:
            return []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Strategy 1: FTS5 MATCH with BM25 ranking
            try:
                tokens = [t for t in clean_q.split() if len(t) > 1]
                fts_query = " OR ".join(f'"{t}"' for t in tokens)
                if fts_query:
                    cur.execute(
                        """
                        SELECT c.id, c.file_path, c.file_name, c.heading, c.line_start, c.line_end, c.content
                        FROM document_chunks c
                        JOIN chunks_fts f ON c.id = f.rowid
                        WHERE chunks_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (fts_query, limit)
                    )
                    rows = cur.fetchall()
                    if rows:
                        return [dict(r) for r in rows]
            except Exception:
                pass

            # Strategy 2: Multi-token LIKE fallback
            tokens = [t for t in clean_q.split() if len(t) > 1]
            if tokens:
                clauses = ["(content LIKE ? OR heading LIKE ? OR file_name LIKE ?)"] * len(tokens)
                where_clause = " OR ".join(clauses)
                params: list[Any] = []
                for t in tokens:
                    pat = f"%{t}%"
                    params.extend([pat, pat, pat])
                params.append(limit)

                cur.execute(
                    f"""
                    SELECT id, file_path, file_name, heading, line_start, line_end, content
                    FROM document_chunks
                    WHERE {where_clause}
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    params
                )
                return [dict(r) for r in cur.fetchall()]
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get total indexed documents and chunks stats."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(DISTINCT file_path), COUNT(*) FROM document_chunks")
            files_c, chunks_c = cur.fetchone() or (0, 0)
            return {"total_files": files_c, "total_chunks": chunks_c}


# Global RAG Engine instance
rag_engine = LocalRAGEngine()
