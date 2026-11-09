"""Tools for interacting with Apex Tiered Cognitive Memory."""
from __future__ import annotations

from typing import Any, Dict, Optional
from apex.memory.tiered import tiered_memory


def manage_cognitive_memory(
    action: str,
    content: str = "",
    memory_type: str = "fact",
    key: str = "",
    importance: int = 5,
    query: str = "",
    pinned: bool = False,
    identifier: str = "",
    limit: int = 5
) -> str:
    """Store, recall, list, and manage long-term cognitive memories, user preferences, and learned rules.

    Args:
        action: One of 'remember', 'recall', 'get_pinned', 'list', 'forget'.
        content: The information, rule, or preference to store (for 'remember').
        memory_type: Type of memory: 'fact', 'preference', 'episode', or 'rule'.
        key: Unique reference slug (optional, e.g. 'user_language_preference').
        importance: Integer priority from 1 (minor detail) to 10 (critical core fact).
        query: Search term for semantic/keyword retrieval (for 'recall').
        pinned: Whether this memory should be pinned and always injected into the system prompt.
        identifier: Numeric ID or key to delete (for 'forget').
        limit: Number of results to return.

    Returns:
        Structured Markdown response.
    """
    act = action.strip().lower()

    if act == "remember":
        if not content:
            return "❌ Parameter 'content' wajib diisi untuk menyimpan memori."
        try:
            mem_id = tiered_memory.remember(
                content=content,
                memory_type=memory_type,
                key=key,
                importance=importance,
                pinned=pinned
            )
            pin_badge = "📌 [PINNED]" if pinned else ""
            return f"🧠 Memori kognitif tersimpan (ID: #{mem_id}) {pin_badge}\n- **Tipe**: `{memory_type}`\n- **Importance**: {importance}/10\n- **Konten**: {content}"
        except Exception as e:
            return f"❌ Gagal menyimpan memori: {e}"

    elif act == "recall":
        if not query:
            return "❌ Parameter 'query' wajib diisi untuk mencari memori."
        results = tiered_memory.recall(query=query, limit=limit, memory_type=memory_type if memory_type != "fact" else None)
        if not results:
            return f"🔍 Tidak ada memori kognitif yang cocok dengan query: '{query}'."

        lines = [f"🧠 **Hasil Temuan Memori Kognitif untuk '{query}'**:"]
        for r in results:
            badge = "📌 " if r["pinned"] else ""
            k_str = f" (`{r['key']}`)" if r.get("key") else ""
            lines.append(f"- {badge}[ID #{r['id']} | `{r['memory_type']}` | Skor: {r['score']}]{k_str}: {r['content']}")
        return "\n".join(lines)

    elif act == "get_pinned":
        pinned_mems = tiered_memory.get_pinned()
        if not pinned_mems:
            return "📭 Belum ada preferensi atau aturan yang di-pin (pinned) di memori."
        lines = ["📌 **Preferensi & Aturan Kognitif yang Di-Pin (Always-Active)**:"]
        for r in pinned_mems:
            k_str = f" (`{r['key']}`)" if r.get("key") else ""
            lines.append(f"- [#{r['id']} | `{r['memory_type']}` | Priority: {r['importance']}]{k_str}: {r['content']}")
        return "\n".join(lines)

    elif act == "list":
        mems = tiered_memory.list_all(limit=limit)
        if not mems:
            return "📭 Database memori kognitif masih kosong."
        rows = [
            "| ID | Tipe | Key | Pinned | Importance | Konten |",
            "| --- | --- | --- | --- | --- | --- |"
        ]
        for m in mems:
            c_preview = m["content"][:60].replace("\n", " ") + ("..." if len(m["content"]) > 60 else "")
            rows.append(f"| #{m['id']} | `{m['memory_type']}` | {m.get('key') or '-'} | {'Yes' if m['pinned'] else 'No'} | {m['importance']} | {c_preview} |")
        return "🧠 **Daftar Memori Kognitif Apex**:\n\n" + "\n".join(rows)

    elif act == "forget":
        if not identifier:
            return "❌ Parameter 'identifier' (ID numerik atau key) wajib diisi untuk menghapus memori."
        ok = tiered_memory.forget(identifier)
        if ok:
            return f"🗑️ Memori `{identifier}` berhasil dihapus dari database kognitif."
        return f"⚠️ Memori `{identifier}` tidak ditemukan."

    else:
        return f"❌ Action `{action}` tidak dikenal. Gunakan: 'remember', 'recall', 'get_pinned', 'list', atau 'forget'."
