"""Shared SQLite Data Lake & Multi-Agent Relational Store (OpenBot Style).

Provides a unified relational SQLite database at `~/.apex/agent_data.db` where autonomous
agents and subagents can create structured tables, store datasets, and execute cross-agent
SQL joins with built-in SQLite security boundaries.
"""
from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from apex.config import DATA_DIR

DATA_LAKE_PATH = DATA_DIR / "agent_data.db"


class SharedDataLake:
    """Manages cross-agent shared relational data lake."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or DATA_LAKE_PATH
        self._init_lake()

    def _init_lake(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS apex_metadata (
                    table_name TEXT PRIMARY KEY,
                    owner_agent TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    description TEXT
                )
            """)
            conn.commit()

    def _format_markdown_table(self, headers: List[str], rows: List[List[Any]]) -> str:
        if not headers:
            return "*(Tabel kosong tanpa kolom)*"
        header_line = "| " + " | ".join(str(h) for h in headers) + " |"
        separator_line = "| " + " | ".join("---" for _ in headers) + " |"
        row_lines = []
        for r in rows:
            row_str = "| " + " | ".join(str(val).replace("\n", " ") for val in r) + " |"
            row_lines.append(row_str)
        return "\n".join([header_line, separator_line] + row_lines)

    def _validate_sql_safety(self, sql: str) -> Tuple[bool, str]:
        """Verify query does not attempt forbidden commands (ATTACH, PRAGMA database escape)."""
        clean_upper = sql.upper()
        # Scan words
        forbidden = ["ATTACH ", "PRAGMA "]
        for f in forbidden:
            if f in clean_upper:
                return False, f"Perintah `{f.strip()}` dilarang pada Shared Data Lake demi keamanan sistem."
        return True, ""

    def query(self, sql: str, agent_id: str = "apex") -> str:
        """Execute query on the shared data lake."""
        if not sql or not sql.strip():
            return "⚠️ Mohon sertakan perintah SQL untuk dieksekusi."

        is_safe, err = self._validate_sql_safety(sql)
        if not is_safe:
            return f"❌ Keamanan: {err}"

        start_t = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Check if statement creates a table to track ownership
                create_match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", sql, re.I)
                if create_match:
                    created_table = create_match.group(1).lower()
                    cursor.execute(sql)
                    cursor.execute("""
                        INSERT OR REPLACE INTO apex_metadata (table_name, owner_agent, created_at, description)
                        VALUES (?, ?, ?, ?)
                    """, (created_table, agent_id, time.time(), f"Created by agent {agent_id}"))
                    conn.commit()
                    elapsed = round((time.time() - start_t) * 1000, 2)
                    return f"✅ **Tabel `{created_table}` berhasil dibuat** di Shared Data Lake oleh agen `{agent_id}` ({elapsed} ms)."

                # Check if it's a SELECT query
                trimmed = sql.strip().upper()
                if trimmed.startswith("SELECT ") or trimmed.startswith("WITH "):
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    elapsed = round((time.time() - start_t) * 1000, 2)
                    if not rows:
                        return f"📊 **Hasil Query SQL** ({elapsed} ms):\n*(0 baris ditemukan — query tidak menghasilkan data)*"

                    headers = list(rows[0].keys())
                    data = [[row[h] for h in headers] for row in rows[:100]]
                    table_md = self._format_markdown_table(headers, data)
                    count_note = f" (menampilkan {len(data)} baris)" if len(rows) > len(data) else f" ({len(data)} baris)"
                    return f"📊 **Hasil Query SQL Shared Data Lake**{count_note} · {elapsed} ms:\n\n{table_md}"

                # Mutating query (INSERT, UPDATE, DELETE, DROP)
                cursor.execute(sql)
                affected = cursor.rowcount
                conn.commit()
                elapsed = round((time.time() - start_t) * 1000, 2)

                drop_match = re.search(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([a-zA-Z0-9_]+)", sql, re.I)
                if drop_match:
                    dropped_table = drop_match.group(1).lower()
                    cursor.execute("DELETE FROM apex_metadata WHERE table_name = ?", (dropped_table,))
                    conn.commit()
                    return f"🗑️ **Tabel `{dropped_table}` berhasil dihapus** dari Shared Data Lake ({elapsed} ms)."

                return f"✅ **Operasi SQL Berhasil**: {affected} baris terpengaruh ({elapsed} ms)."

        except Exception as e:
            return f"❌ SQL Error: {str(e)}"

    def list_tables(self) -> str:
        """List all shared tables with metadata and record counts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name != 'apex_metadata'
                    ORDER BY name ASC
                """)
                tables = [r["name"] for r in cur.fetchall()]

                if not tables:
                    return (
                        f"🗄️ **Apex Shared Data Lake** (`{self.db_path.name}`):\n"
                        f"*(Belum ada tabel data yang dibuat oleh agen)*\n\n"
                        f"💡 Anda dapat membuat tabel baru menggunakan `manage_data_lake(action='query', query='CREATE TABLE ...')`."
                    )

                meta_dict = {}
                cur.execute("SELECT table_name, owner_agent, created_at FROM apex_metadata")
                for r in cur.fetchall():
                    meta_dict[r["table_name"]] = (r["owner_agent"], r["created_at"])

                lines = [f"🗄️ **Daftar Tabel di Shared Data Lake ({len(tables)} Tabel)**:\n"]
                for t in tables:
                    cur.execute(f"SELECT COUNT(*) as cnt FROM {t}")
                    cnt = cur.fetchone()["cnt"]
                    owner, created = meta_dict.get(t, ("unknown", 0))
                    created_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(created)) if created else "-"
                    lines.append(f"• **`{t}`**: **{cnt} baris** (Owner: `{owner}`, dibuat: `{created_str}`)")

                lines.append(
                    "\n💡 *Gunakan `manage_data_lake(action='query', query='SELECT ... FROM <table>')` untuk membaca data.*"
                )
                return "\n".join(lines)
        except Exception as e:
            return f"❌ Gagal membaca daftar tabel: {str(e)}"

    def describe_table(self, table_name: str) -> str:
        """Show schema structure and columns of a shared table."""
        clean_table = table_name.strip().lower()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(f"PRAGMA table_info({clean_table})")
                cols = cur.fetchall()
                if not cols:
                    return f"❌ Tabel `{clean_table}` tidak ditemukan di Shared Data Lake."

                lines = [f"📋 **Struktur Kolom Tabel `{clean_table}`**:\n"]
                for c in cols:
                    c_name = c["name"]
                    c_type = c["type"] or "TEXT"
                    is_pk = " 🔑 *(PRIMARY KEY)*" if c["pk"] else ""
                    not_null = " *(NOT NULL)*" if c["notnull"] else ""
                    lines.append(f"• **`{c_name}`** ({c_type}){is_pk}{not_null}")
                return "\n".join(lines)
        except Exception as e:
            return f"❌ Gagal menginspeksi tabel `{clean_table}`: {str(e)}"


# Global shared data lake instance
shared_data_lake = SharedDataLake()
