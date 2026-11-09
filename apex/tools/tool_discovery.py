"""Dynamic Tool Discovery, Deferred Loading & Schema Inspector (OpenBot Style).

Enables massive token savings by keeping only core tools in the initial context payload,
while specialized tools (network diagnostic, devops, database, reverse engineering, scrapers)
are searched and loaded on-demand via `tool_search` and `tool_describe`.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple


class ToolDiscoveryService:
    """Provides semantic and keyword discovery over registered tools."""

    def __init__(self) -> None:
        pass

    def search(
        self,
        tools_dict: Dict[str, Dict[str, Any]],
        query: str,
        max_results: int = 5
    ) -> str:
        """Search registered tools by keyword matching against names and descriptions.

        Returns:
            Structured Markdown guide with ready-to-call schemas for strong matches.
        """
        if not query or not query.strip():
            return "⚠️ Mohon sertakan kata kunci pencarian tool (contoh: `dns`, `ssl`, `database`, `test`)."

        q_clean = query.strip().lower()
        q_words = set(re.findall(r"\w+", q_clean))

        scored: List[Tuple[int, str, Dict[str, Any]]] = []

        for name, t_data in tools_dict.items():
            name_lower = name.lower()
            desc_lower = t_data.get("description", "").lower()
            score = 0

            # 1. Exact name match
            if q_clean == name_lower:
                score += 150
            elif q_clean in name_lower:
                score += 60

            # 2. Word matches in name
            name_words = set(re.findall(r"\w+", name_lower))
            matched_name_words = q_words.intersection(name_words)
            score += len(matched_name_words) * 25

            # 3. Word matches in description
            desc_words = set(re.findall(r"\w+", desc_lower))
            matched_desc_words = q_words.intersection(desc_words)
            score += len(matched_desc_words) * 8

            if score > 0:
                scored.append((score, name, t_data))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = scored[:max_results]

        if not results:
            return (
                f"🔍 **Pencarian Tool (`{query}`)**: Tidak ada tool yang cocok secara langsung.\n\n"
                f"💡 *Tips*: Coba kata kunci yang lebih umum seperti `file`, `shell`, `web`, `git`, `network`, atau `db`."
            )

        output_lines = [
            f"🔍 **Hasil Pencarian Tool Apex (`{query}`)** — Ditemukan {len(results)} tool relevan:\n"
        ]

        for rank, (score, name, t_data) in enumerate(results, 1):
            desc = t_data.get("description", "")
            params = t_data.get("parameters", {})
            props = params.get("properties", {})
            required = params.get("required", [])

            # Format parameters summary
            param_list = []
            for p_name, p_spec in props.items():
                p_type = p_spec.get("type", "any")
                req_badge = " *(wajib)*" if p_name in required else ""
                param_list.append(f"`{p_name}` ({p_type}{req_badge})")
            param_str = ", ".join(param_list) if param_list else "tanpa parameter"

            # If top match is strong, embed ready schema for immediate invocation
            if rank <= 2 or score >= 40:
                schema_json = json.dumps({
                    "name": name,
                    "description": desc,
                    "parameters": params
                }, indent=2)
                output_lines.append(
                    f"### #{rank}. `{name}` (Skor: {score})\n"
                    f"• **Deskripsi**: {desc}\n"
                    f"• **Parameter**: {param_str}\n"
                    f"• **Skema Siap Pakai**:\n```json\n{schema_json}\n```\n"
                )
            else:
                output_lines.append(
                    f"• **`{name}`**: {desc}\n  *Parameter*: {param_str}\n"
                )

        output_lines.append(
            "\n💡 *Instruksi*: Anda dapat langsung memanggil tool di atas dengan nama fungsinya "
            "atau memanggil `tool_describe(tool_name='...')` untuk panduan lebih lanjut."
        )

        return "\n".join(output_lines)

    def describe(
        self,
        tools_dict: Dict[str, Dict[str, Any]],
        tool_name: str
    ) -> str:
        """Inspect detailed parameters, types, and schema of a registered tool."""
        clean_name = tool_name.strip()
        if clean_name not in tools_dict:
            # Try fuzzy match
            candidates = [n for n in tools_dict.keys() if clean_name.lower() in n.lower()]
            if candidates:
                cand_str = ", ".join(f"`{c}`" for c in candidates[:4])
                return f"❌ Tool `{clean_name}` tidak ditemukan. Mungkin maksud Anda: {cand_str}?"
            return f"❌ Tool `{clean_name}` tidak terdaftar dalam registry Apex."

        t_data = tools_dict[clean_name]
        desc = t_data.get("description", "")
        params = t_data.get("parameters", {})
        props = params.get("properties", {})
        required = set(params.get("required", []))
        is_safe = t_data.get("is_safe", False)

        badge_safety = "🟢 Safe (Read-Only / Parallelizable)" if is_safe else "🟠 Mutating (Requires sequential lock)"

        lines = [
            f"🛠️ **Inspeksi Detail Tool: `{clean_name}`**\n",
            f"• **Deskripsi**: {desc}",
            f"• **Tipe Eksekusi**: {badge_safety}",
            f"\n### 📋 Parameter Spesifikasi:\n"
        ]

        if not props:
            lines.append("*(Tool ini tidak memerlukan parameter)*")
        else:
            for p_name, p_spec in props.items():
                p_type = p_spec.get("type", "any")
                p_desc = p_spec.get("description", "Tidak ada deskripsi")
                p_default = p_spec.get("default")
                req_str = "🔴 **Wajib**" if p_name in required else "⚪ Opsional"
                default_str = f" · Default: `{repr(p_default)}`" if p_default is not None else ""
                lines.append(f"• **`{p_name}`** ({p_type}) — {req_str}{default_str}\n  {p_desc}")

        schema_json = json.dumps({
            "name": clean_name,
            "description": desc,
            "parameters": params
        }, indent=2)

        lines.append(f"\n### 📄 Skema JSON Kompatibel LLM:\n```json\n{schema_json}\n```")
        return "\n".join(lines)


# Global discovery service
tool_discovery = ToolDiscoveryService()
