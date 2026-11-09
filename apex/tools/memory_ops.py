"""Memory & Knowledge Base Tools for Apex."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from apex.memory.store import memory_store
from apex.memory.rag import rag_engine


def remember_fact(content: str, category: str = "general", tags: str = "") -> str:
    """Store an important fact, user preference, architecture decision, or lesson into long-term memory.

    Args:
        content: The fact or lesson to remember.
        category: Category (e.g. 'preference', 'architecture', 'credential', 'project').
        tags: Comma-separated tags for fast discovery.

    Returns:
        Confirmation message with assigned memory ID.
    """
    clean_c = content.strip()
    if not clean_c:
        return "❌ Konten memori kosong."

    entry_id = memory_store.store(clean_c, category=category, tags=tags)
    return f"🧠 **Memori Tersimpan**: Fact #{entry_id} tersimpan dalam kategori `{category}` [tags: {tags or 'none'}]."


def recall_memory(query: str, limit: int = 5) -> str:
    """Recall or search stored facts and long-term memories using semantic full-text search.

    Args:
        query: Keyword or phrase to search in memory.
        limit: Maximum number of memories to return (default: 5).

    Returns:
        Structured list of matching memories.
    """
    results = memory_store.search(query, limit=limit)
    if not results:
        return f"🔍 Tidak ditemukan memori jangka panjang yang cocok dengan kata kunci: `{query}`."

    lines = [f"🧠 **Hasil Penelusuran Memori Jangka Panjang (`{len(results)}` ditemukan)**:\n"]
    for idx, r in enumerate(results, 1):
        cat = r.get("category", "general")
        content = r.get("content", "")
        tags = r.get("tags", "")
        tags_disp = f" *(tags: {tags})*" if tags else ""
        lines.append(f"{idx}. `[{cat.upper()}]` {content}{tags_disp}")

    return "\n".join(lines)


def index_knowledge_base(path: str, max_files: int = 100) -> str:
    """Index an entire folder or document into Apex's local RAG semantic search knowledge base.

    Supports indexing source code, markdown docs, PDF, Word, Excel, and configuration files.

    Args:
        path: Path to file or directory to index (e.g. 'docs/', 'src/', 'README.md').
        max_files: Maximum number of files to index (default: 100).

    Returns:
        Summary of indexed files and chunks.
    """
    res = rag_engine.index_path(path, max_files=max_files)
    if not res.get("success"):
        return f"❌ Gagal mengindeks: {res.get('error')}"

    return (
        f"📚 **Knowledge Base Berhasil Diperbarui** 🚀\n\n"
        f"• Target Path: `{res['target']}`\n"
        f"• Berkas Terindeks: **{res['files_indexed']}** berkas\n"
        f"• Chunks Teks FTS5: **{res['chunks_created']}** potongan konten\n"
        f"• Waktu Pemrosesan: **{res['elapsed_seconds']}s**"
    )


def search_knowledge_base(query: str, limit: int = 5) -> str:
    """Search the local RAG knowledge base for specific information across indexed project files.

    Args:
        query: Question or technical keyword to locate.
        limit: Maximum number of relevant code/doc chunks to retrieve (default: 5).

    Returns:
        Snippets of matching documents with file path and line number citations.
    """
    results = rag_engine.search(query, limit=limit)
    if not results:
        return f"📚 Tidak ditemukan potongan dokumen yang cocok dengan `{query}` di Knowledge Base."

    sections = [f"📚 **Hasil Pencarian Knowledge Base (RAG) untuk: `{query}`**\n"]
    for idx, r in enumerate(results, 1):
        fname = r.get("file_name", "doc")
        fpath = r.get("file_path", "")
        heading = r.get("heading", "")
        l_start = r.get("line_start", 1)
        l_end = r.get("line_end", 1)
        content = r.get("content", "")

        sections.append(
            f"### #{idx}: `{fname}` (Baris {l_start}-{l_end}) [Bagian: *{heading}*]\n"
            f"> Path: `{fpath}`\n\n"
            f"```\n{content}\n```"
        )

    return "\n\n---\n\n".join(sections)
