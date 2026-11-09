"""Dedicated Database Explorer & SQL Query Tool for Apex."""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _format_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Format headers and rows into a clean Markdown table."""
    if not headers:
        return "*(Tabel kosong tanpa kolom)*"
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    row_lines = []
    for r in rows:
        row_str = "| " + " | ".join(str(val).replace("\n", " ") for val in r) + " |"
        row_lines.append(row_str)
    return "\n".join([header_line, separator_line] + row_lines)


def query_database(
    database: str,
    query: Optional[str] = None,
    limit: int = 50
) -> str:
    """Inspect database schema or execute SQL query on a SQLite database.

    Args:
        database: Path to the SQLite database file (e.g. 'users.db', '~/.apex/memory.db').
        query: Optional SQL query to execute. If omitted or empty, inspects and returns table schemas.
        limit: Maximum number of rows to return (default: 50).

    Returns:
        Formatted Markdown table of results, affected row count, or schema listing.
    """
    db_path = Path(os.path.expanduser(database))
    if not db_path.exists():
        return f"❌ Database file tidak ditemukan di jalur: `{db_path}`"

    start_t = time.time()
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # If query is None or empty, inspect database schema
        if not query or not query.strip():
            cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name;")
            tables = cursor.fetchall()
            if not tables:
                conn.close()
                return f"📊 **Database Schema:** `{db_path.name}`\n*(Database tidak memiliki tabel atau kosong)*"

            output_sections = [f"📊 **Database Schema & Table Listing: `{db_path.name}`**\n"]
            for t in tables:
                t_name = t["name"]
                t_type = t["type"].upper()
                cursor.execute(f"PRAGMA table_info('{t_name}');")
                cols = cursor.fetchall()
                col_defs = [f"`{c['name']}` ({c['type'] or 'ANY'})" + (" [PK]" if c["pk"] else "") for c in cols]
                output_sections.append(f"• **{t_type} `{t_name}`**: {', '.join(col_defs) if col_defs else 'tanpa kolom'}")

            conn.close()
            elapsed = round(time.time() - start_t, 3)
            return "\n".join(output_sections) + f"\n\n*(Ditemukan {len(tables)} objek tabel/view dalam {elapsed}s)*"

        # Execute provided query
        clean_query = query.strip()
        is_select = clean_query.upper().startswith(("SELECT", "PRAGMA", "EXPLAIN", "WITH"))

        cursor.execute(clean_query)

        if is_select:
            rows = cursor.fetchmany(limit)
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            table_md = _format_markdown_table(col_names, [list(r) for r in rows])
            elapsed = round(time.time() - start_t, 3)
            conn.close()
            return (
                f"✅ **Hasil Query SQL** (`{elapsed}s`):\n"
                f"```sql\n{clean_query}\n```\n\n"
                f"{table_md}\n\n"
                f"*(Menampilkan {len(rows)} baris, limit: {limit})*"
            )
        else:
            conn.commit()
            affected = cursor.rowcount
            elapsed = round(time.time() - start_t, 3)
            conn.close()
            return (
                f"✅ **Operasi SQL Berhasil Dieksekusi** (`{elapsed}s`):\n"
                f"```sql\n{clean_query}\n```\n\n"
                f"• Baris terpengaruh (*rows affected*): **{affected}**"
            )

    except Exception as e:
        return f"❌ Kesalahan SQL saat mengeksekusi pada `{db_path.name}`: {str(e)}"
