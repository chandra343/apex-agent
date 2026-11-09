"""Autonomous AI Provider Management Tool for Project Apex."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from apex.config import config
from apex.router.provider_manager import provider_manager


def manage_ai_providers(
    action: str,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    query: Optional[str] = None
) -> str:
    """Manage, search, switch, test, or add AI providers and models dynamically.

    Supported actions:
    - 'list': List currently configured providers with models and active status.
    - 'search': Search catalog and registered providers by keyword (e.g. 'groq', 'deepseek', 'free', 'coding', 'fast', 'sonnet').
    - 'use': Switch primary active provider and optionally set default model.
    - 'add': Add or configure a provider (with automatic URL/model catalog matching and key verification).
    - 'test': Test connection and latency to a provider (or all configured providers if provider_name is omitted).
    - 'fetch_models': Query live available models from provider upstream endpoint.
    - 'scan_local': Scan localhost for running Ollama, LM Studio, vLLM, or llama.cpp instances.
    - 'remove': Remove a provider from configuration.

    Args:
        action: Operation to perform ('list', 'search', 'use', 'add', 'test', 'fetch_models', 'scan_local', 'remove').
        provider_name: Target provider ID (e.g. 'groq', 'deepseek', 'ollama', 'anthropic').
        api_key: API key or session token when adding/configuring.
        base_url: Custom base URL endpoint (e.g. 'https://api.groq.com/openai/v1' or 'http://localhost:8000/v1').
        model_name: Optional model to activate or add.
        query: Search term when using 'search'.

    Returns:
        Structured execution result with status and guidance.
    """
    act = action.strip().lower()

    if act == "list":
        summary = provider_manager.get_provider_shelf_summary()
        active_p = config.active_provider
        lines = [
            f"🤖 **Daftar Provider AI Terdaftar di Apex** (Aktif: `{active_p.upper()}` | Model: `{config.default_model}`):",
            ""
        ]
        count = 0
        for item in summary:
            if not item.get("is_configured") and not item.get("has_key"):
                continue
            count += 1
            is_act = "★ **(AKTIF)**" if item.get("is_active") else ""
            m_preview = ", ".join(item.get("models", [])[:3])
            lines.append(
                f"• {item.get('icon', '🤖')} **{item['name']}** (`{item['id']}`) {is_act}\n"
                f"  - Kategori: {item.get('category_label', item.get('category'))}\n"
                f"  - Model ({item.get('model_count')} model): `{m_preview}`...\n"
                f"  - Endpoint: `{item.get('url')}`"
            )
        if count == 0:
            lines.append("ℹ️ Belum ada provider eksternal yang terkonfigurasi selain default.")
        return "\n".join(lines)

    elif act == "search":
        q = (query or provider_name or "").strip()
        if not q:
            return "❌ Parameter `query` wajib diisi saat mencari provider (contoh: 'free', 'coding', 'fast', 'groq', 'sonnet')."
        matches = provider_manager.search_providers(q)
        if not matches:
            return f"ℹ️ Tidak ditemukan provider atau model yang cocok dengan kata kunci `{q}`."
        lines = [f"🔍 **Hasil Pencarian Provider AI untuk `{q}` ({len(matches)} hasil)**:", ""]
        for m in matches:
            badge = "★ **[AKTIF]**" if m.get("is_active") else ("🟢 [Siap Digunakan]" if m.get("is_configured") else "⚪ [Tersedia di Katalog]")
            reasons = ", ".join(m.get("reasons", []))
            lines.append(
                f"• {m.get('icon', '🤖')} **{m['name']}** (`{m['id']}`) — {badge}\n"
                f"  - Cocok karena: {reasons}\n"
                f"  - Model: `{', '.join(m.get('models', [])[:3])}`...\n"
                f"  - URL: `{m.get('url')}`"
            )
        return "\n".join(lines)

    elif act == "use":
        target_p = (provider_name or "").strip().lower()
        if not target_p:
            return "❌ Parameter `provider_name` wajib diisi saat beralih provider (contoh: 'deepseek', 'ollama', 'groq')."
        ok, msg = provider_manager.set_active_provider(target_p, model_name)
        if ok:
            t_ok, t_msg, t_lat = provider_manager.test_provider(target_p)
            test_info = f"🟢 Uji koneksi: OK ({t_lat}s)" if t_ok else f"⚠️ Peringatan koneksi: {t_msg}"
            return f"✅ **{msg}**\n• Status: {test_info}\n• Model aktif: `{config.default_model}`"
        return f"❌ {msg}"

    elif act == "add":
        target_p = (provider_name or "").strip().lower()
        if not target_p:
            return "❌ Parameter `provider_name` wajib diisi saat menambahkan provider."
        models_list = [model_name.strip()] if model_name else None
        ok, msg, detail = provider_manager.add_provider_smart(
            target_p,
            api_key=api_key or "",
            base_url=base_url or "",
            models=models_list,
            auto_fetch=True,
            verify_now=True
        )
        if ok:
            test_badge = "🟢 Uji koneksi berhasil" if detail.get("test_success") else f"⚠️ Uji koneksi: {detail.get('test_message')}"
            return (
                f"✅ **Provider Berhasil Dikonfigurasi**: `{target_p.upper()}`\n"
                f"• Endpoint: `{detail.get('base_url')}`\n"
                f"• Jumlah Model: {detail.get('models_count')} model (`{', '.join(detail.get('models', [])[:3])}...`)\n"
                f"• Status Verifikasi: {test_badge}"
            )
        return f"❌ Gagal menambahkan provider: {msg}"

    elif act == "test":
        target_p = (provider_name or "").strip().lower()
        if target_p:
            ok, msg, lat = provider_manager.test_provider(target_p)
            badge = "✅ BERHASIL" if ok else "❌ GAGAL"
            return f"{badge} **Uji Koneksi `{target_p.upper()}`** ({lat}s):\n• Respon: {msg}"
        else:
            results = provider_manager.test_all()
            lines = ["📊 **Hasil Uji Seluruh Provider Aktif**:", ""]
            for p, (ok, msg, lat) in results.items():
                badge = "✅" if ok else "❌"
                lines.append(f"• {badge} **{p.upper()}** ({lat}s): {msg}")
            return "\n".join(lines)

    elif act == "fetch_models":
        target_p = (provider_name or "").strip().lower()
        if not target_p:
            return "❌ Parameter `provider_name` wajib diisi saat mengambil daftar model live."
        ok, msg, models = provider_manager.fetch_live_models(target_p)
        if ok:
            return f"✅ **{msg}**\n• Model ({len(models)}): `{', '.join(models[:10])}`"
        return f"❌ {msg}"

    elif act == "scan_local":
        scan_res = provider_manager.scan_and_register_local_engines()
        reg = scan_res.get("registered", [])
        if reg:
            lines = [f"✅ **Ditemukan & Didaftarkan {len(reg)} Engine AI Lokal**:", ""]
            for item in reg:
                lines.append(f"• 🦙 **{item['name']}** di `{item['url']}` (Model: `{', '.join(item['models'][:3])}`)")
            return "\n".join(lines)
        return "ℹ️ Tidak ditemukan engine AI lokal yang sedang aktif di port default (11434, 1234, 8000, 8080)."

    elif act == "remove":
        target_p = (provider_name or "").strip().lower()
        if not target_p:
            return "❌ Parameter `provider_name` wajib diisi saat menghapus provider."
        if provider_manager.remove_provider(target_p):
            return f"✅ **Provider `{target_p}` Berhasil Dihapus dari Konfigurasi**."
        return f"❌ Provider `{target_p}` tidak ditemukan."

    return (
        f"❌ Aksi '{action}' tidak dikenali. "
        "Gunakan: 'list', 'search', 'use', 'add', 'test', 'fetch_models', 'scan_local', atau 'remove'."
    )
