"""Incremental Provider Manager with live Hot-Reloading, 35+ Provider Catalog, and Diagnostics."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from apex.config import config
from apex.router.catalog import FULL_PROVIDER_CATALOG, find_catalog_entry
from apex.router.key_pool import key_pool
from apex.router.oauth_manager import oauth_manager


class ProviderManager:
    """Manages active AI providers, endpoints, key pools, testing, and Copilot sessions."""

    def __init__(self) -> None:
        self.sync_with_config()

    def sync_with_config(self) -> None:
        """Register all configured provider keys into the key pool."""
        providers = config.get("providers", {})
        for name, p_data in providers.items():
            key = p_data.get("api_key", "")
            if key and not key.startswith("YOUR_") and key != "none":
                key_pool.set_keys(name, key)

    def add_provider(
        self,
        name: str,
        api_key: str,
        base_url: str,
        models: List[str]
    ) -> None:
        """Incrementally add or update a provider and hot-reload."""
        providers = config.get("providers", {})
        providers[name] = {
            "api_key": api_key,
            "base_url": base_url,
            "models": models
        }
        config.set("providers", providers, auto_save=True)
        if api_key != "none" and not api_key.startswith("YOUR_"):
            key_pool.set_keys(name, api_key)

    def remove_provider(self, name: str) -> bool:
        """Remove a provider from configuration."""
        providers = config.get("providers", {})
        if name in providers:
            # If removing active provider, fallback to tokenharbor or antigravity
            if name == config.get("active_provider"):
                config.set("active_provider", "tokenharbor", auto_save=False)
            del providers[name]
            config.set("providers", providers, auto_save=True)
            return True
        return False

    def search_providers(self, query: str) -> List[Dict[str, Any]]:
        """Search across catalog and configured providers by keyword, model, or category."""
        q = query.strip().lower()
        if not q:
            return []

        configured = config.get("providers", {})
        active_p = config.get("active_provider", "").lower()
        results: List[Dict[str, Any]] = []
        seen_ids = set()

        is_free_intent = q in ["free", "gratis", "free-tier"]
        is_local_intent = q in ["local", "lokal", "offline", "self-hosted"]
        is_fast_intent = q in ["fast", "cepat", "speed", "latency"]
        is_coding_intent = q in ["coding", "code", "coder", "programmer"]

        for item in FULL_PROVIDER_CATALOG:
            p_id = item["id"].lower()
            name = item["name"].lower()
            cat = item.get("category", "").lower()
            desc = item.get("description", "").lower()
            models = [m.lower() for m in item.get("models", [])]

            matched = False
            reasons = []

            if q in p_id or q in name:
                matched = True
                reasons.append("Nama/ID Provider")
            elif any(q in m for m in models):
                matched = True
                matching_m = [m for m in item.get("models", []) if q in m.lower()]
                reasons.append(f"Model: {', '.join(matching_m[:2])}")
            elif q in cat or q in desc:
                matched = True
                reasons.append(f"Kategori: {cat}")
            elif is_free_intent and (p_id in ["tokenharbor", "antigravity", "kiro", "ollama", "vllm", "lmstudio", "localai", "gemini-free"] or any(":free" in m for m in models)):
                matched = True
                reasons.append("Tersedia Free-Tier / Gratis")
            elif is_local_intent and (cat == "local" or p_id in ["ollama", "vllm", "lmstudio", "llamacpp", "localai"]):
                matched = True
                reasons.append("Engine AI Lokal / Offline")
            elif is_fast_intent and (cat == "fast" or p_id in ["groq", "cerebras", "sambanova", "together", "fireworks", "siliconflow"]):
                matched = True
                reasons.append("Ultra Fast Inference")
            elif is_coding_intent and (p_id in ["copilot", "claude-code", "antigravity", "openai", "deepseek", "cursor", "mistral"] or any("coder" in m or "code" in m for m in models)):
                matched = True
                reasons.append("Optimal untuk Coding & Agentic Tools")

            if matched:
                seen_ids.add(p_id)
                cfg = configured.get(p_id, {})
                has_key = bool(cfg.get("api_key") and cfg.get("api_key") != "none")
                results.append({
                    "id": p_id,
                    "name": item["name"],
                    "icon": item.get("icon", "🤖"),
                    "category": item.get("category", "frontier"),
                    "auth_type": item.get("auth_type", "api_key"),
                    "url": cfg.get("base_url") or item.get("url", ""),
                    "models": cfg.get("models") or item.get("models", []),
                    "is_active": (p_id == active_p),
                    "is_configured": self.is_provider_configured(p_id),
                    "has_key": has_key,
                    "reasons": reasons,
                    "description": item.get("description", "")
                })

        for p_id, p_data in configured.items():
            if p_id in seen_ids:
                continue
            p_id_l = p_id.lower()
            models_l = [m.lower() for m in p_data.get("models", [])]
            if q in p_id_l or any(q in m for m in models_l):
                results.append({
                    "id": p_id,
                    "name": p_id.upper(),
                    "icon": "🔌",
                    "category": "custom",
                    "auth_type": "custom",
                    "url": p_data.get("base_url", ""),
                    "models": p_data.get("models", []),
                    "is_active": (p_id == active_p),
                    "is_configured": self.is_provider_configured(p_id),
                    "has_key": bool(p_data.get("api_key")),
                    "reasons": ["Custom Registered Provider"],
                    "description": "Custom registered provider"
                })

        return results

    def add_provider_smart(
        self,
        name: str,
        api_key: str = "",
        base_url: str = "",
        models: Optional[List[str]] = None,
        auto_fetch: bool = True,
        verify_now: bool = True
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Smart addition/update of an AI provider with catalog auto-fill, env lookup, and live verification."""
        import os
        p_id = name.strip().lower()
        if not p_id:
            return False, "Nama atau ID provider tidak boleh kosong.", {}

        catalog_entry = find_catalog_entry(p_id)
        final_url = base_url.strip() if base_url else (catalog_entry.get("url", "") if catalog_entry else "http://localhost:8000/v1")
        final_models = list(models) if models else (list(catalog_entry.get("models", [])) if catalog_entry else [f"{p_id}-model"])

        final_key = api_key.strip()
        if not final_key and (not catalog_entry or catalog_entry.get("auth_type") != "none"):
            env_candidates = [
                f"{p_id.upper().replace('-', '_')}_API_KEY",
                f"{p_id.upper().replace('-', '_')}_KEY",
                f"{p_id.upper().replace('-', '_')}_TOKEN"
            ]
            for cand in env_candidates:
                val = os.environ.get(cand)
                if val:
                    final_key = val
                    break

        if not final_key and catalog_entry and catalog_entry.get("auth_type") == "none":
            final_key = "none"

        self.add_provider(p_id, final_key, final_url, final_models)

        fetched_count = 0
        if auto_fetch and (final_key or p_id in ["ollama", "vllm", "lmstudio", "llamacpp"]):
            fetch_ok, fetch_msg, live_models = self.fetch_live_models(p_id)
            if fetch_ok and live_models:
                final_models = live_models
                fetched_count = len(live_models)

        test_ok, test_msg, test_lat = False, "Not tested", 0.0
        if verify_now and (final_key != "" or p_id in ["ollama", "vllm", "lmstudio", "llamacpp"]):
            test_ok, test_msg, test_lat = self.test_provider(p_id)

        detail = {
            "id": p_id,
            "base_url": final_url,
            "models": final_models,
            "models_count": len(final_models),
            "has_key": bool(final_key and final_key != "none"),
            "fetched_models": fetched_count,
            "test_success": test_ok,
            "test_message": test_msg,
            "test_latency": test_lat
        }

        msg = f"Provider '{p_id}' berhasil dikonfigurasi ({len(final_models)} model)."
        if verify_now:
            if test_ok:
                msg += f" Uji koneksi: OK ({test_lat}s)."
            else:
                msg += f" Peringatan uji koneksi: {test_msg}."

        return True, msg, detail

    def get_provider_shelf_summary(self, category: str = "all") -> List[Dict[str, Any]]:
        """Return structured summary of all providers for UI/UX rendering."""
        from apex.router.catalog import get_providers_by_category, PROVIDER_CATEGORIES
        configured = config.get("providers", {})
        active_p = config.get("active_provider", "").lower()
        items = []
        known_ids = set()

        cat_list = get_providers_by_category(category)
        for cat_item in cat_list:
            p_id = cat_item["id"].lower()
            known_ids.add(p_id)
            cfg = configured.get(p_id, {})
            key = cfg.get("api_key", "")
            has_key = bool(key and key != "none")
            masked = (key[:4] + "••••••••" + key[-4:]) if (has_key and len(key) > 8) else ("none" if key == "none" else ("••••••" if has_key else ""))
            models = cfg.get("models") or cat_item.get("models", [])
            orig_cat = cat_item.get("category", "api_key")
            if orig_cat in ["frontier", "fast", "apac", "cloud", "agg"]:
                mapped_cat = "api_key"
            else:
                mapped_cat = orig_cat

            items.append({
                "id": p_id,
                "name": cat_item["name"],
                "icon": cat_item.get("icon", "🤖"),
                "category": mapped_cat,
                "category_label": PROVIDER_CATEGORIES.get(cat_item.get("category", ""), ""),
                "auth_type": cat_item.get("auth_type", "api_key"),
                "url": cfg.get("base_url") or cat_item.get("url", ""),
                "models": models,
                "model_count": len(models),
                "is_active": (p_id == active_p),
                "is_configured": self.is_provider_configured(p_id),
                "has_key": has_key,
                "masked_key": masked,
                "description": cat_item.get("description", "")
            })

        if category in ["all", "local", "compatible"]:
            for c_id, c_data in configured.items():
                if c_id.lower() not in known_ids:
                    key = c_data.get("api_key", "")
                    has_key = bool(key and key != "none")
                    masked = (key[:4] + "••••••••" + key[-4:]) if (has_key and len(key) > 8) else ("none" if key == "none" else ("••••••" if has_key else ""))
                    models = c_data.get("models", [f"{c_id}-model"])
                    items.append({
                        "id": c_id,
                        "name": c_id.upper(),
                        "icon": "🔌",
                        "category": "compatible",
                        "category_label": "API Key Compatible Provider",
                        "auth_type": "compatible",
                        "url": c_data.get("base_url", "-"),
                        "models": models,
                        "model_count": len(models),
                        "is_active": (c_id == active_p),
                        "is_configured": self.is_provider_configured(c_id),
                        "has_key": has_key,
                        "masked_key": masked,
                        "description": "Custom registered compatible provider"
                    })
        return items

    def scan_and_register_local_engines(self) -> Dict[str, Any]:
        """Scan localhost for Ollama, LM Studio, vLLM, etc., and register found engines."""
        detected = oauth_manager.scan_local_services()
        configured = config.get("providers", {})
        registered = []
        for p_id, info in detected.items():
            models = info.get("models", [f"{p_id}-model"])
            configured[p_id] = {
                "api_key": "none",
                "base_url": info.get("base_url", ""),
                "models": models
            }
            registered.append({"id": p_id, "name": info.get("name"), "url": info.get("base_url"), "models": models})
        if registered:
            config.set("providers", configured, auto_save=True)
        return {"detected": detected, "registered": registered, "count": len(registered)}

    def add_model_to_provider(self, provider_name: str, model_name: str) -> Tuple[bool, str]:
        """Add a custom user model to a specific provider and save config."""
        p_name = provider_name.strip().lower()
        m_name = model_name.strip()
        if not m_name:
            return False, "Nama model tidak boleh kosong."

        providers = config.get("providers", {})
        if p_name not in providers:
            providers[p_name] = {
                "api_key": "none",
                "base_url": "http://localhost:8000/v1",
                "models": []
            }

        curr_models = providers[p_name].get("models", [])
        if m_name in curr_models or any(m.lower() == m_name.lower() for m in curr_models):
            return False, f"Model '{m_name}' sudah terdaftar pada provider '{p_name}'."

        curr_models.append(m_name)
        providers[p_name]["models"] = curr_models
        config.set("providers", providers, auto_save=True)
        return True, f"Model '{m_name}' berhasil ditambahkan ke provider '{p_name}'!"

    def remove_model_from_provider(self, provider_name: str, model_name: str) -> Tuple[bool, str]:
        """Remove a model from a specific provider and save config."""
        p_name = provider_name.strip().lower()
        m_name = model_name.strip().lower()
        if not m_name:
            return False, "Nama model tidak boleh kosong."

        providers = config.get("providers", {})
        if p_name not in providers:
            return False, f"Provider '{p_name}' tidak ditemukan."

        curr_models = providers[p_name].get("models", [])
        found_target = None
        for m in curr_models:
            if m.lower() == m_name:
                found_target = m
                break

        if not found_target:
            return False, f"Model '{model_name}' tidak ditemukan di provider '{p_name}'."

        curr_models.remove(found_target)
        providers[p_name]["models"] = curr_models
        config.set("providers", providers, auto_save=True)
        return True, f"Model '{found_target}' berhasil dihapus dari provider '{p_name}'."

    def set_active_provider(self, provider_name: str, model_name: Optional[str] = None) -> Tuple[bool, str]:
        """Set the designated primary provider and default model to use."""
        p_name = provider_name.strip().lower()
        providers = config.get("providers", {})
        if p_name not in providers:
            return False, f"Provider '{p_name}' belum terdaftar di konfigurasi."

        p_data = providers[p_name]
        p_models = p_data.get("models", [])

        target_model = model_name.strip() if model_name else ""
        if not target_model:
            target_model = p_models[0] if p_models else config.default_model

        config.set("active_provider", p_name, auto_save=False)
        config.set("default_model", target_model, auto_save=True)
        return True, f"Provider aktif diatur ke '{p_name}' dengan model '{target_model}'!"

    def get_provider_for_model(self, model_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find the matching provider configuration for a given model."""
        providers = config.get("providers", {})
        model_lower = model_name.lower()

        # 0. Check if designated active_provider can serve this model
        active_p = config.get("active_provider")
        if active_p and active_p in providers:
            active_cfg = providers[active_p]
            active_models = [m.lower() for m in active_cfg.get("models", [])]
            if model_lower in active_models:
                return active_p, active_cfg

        # 1. Exact match in model list of configured providers
        for name, p_data in providers.items():
            models = [m.lower() for m in p_data.get("models", [])]
            if model_lower in models:
                return name, p_data

        # 2. Check if GitHub Copilot is configured and can handle the model
        if "copilot" in providers:
            copilot_cfg = providers["copilot"]
            copilot_models = [m.lower() for m in copilot_cfg.get("models", [])]
            if any(cm in model_lower or model_lower in cm for cm in copilot_models):
                return "copilot", copilot_cfg

        # 3. Check if Google Antigravity is configured and can handle the model
        if "antigravity" in providers:
            ag_cfg = providers["antigravity"]
            ag_models = [m.lower() for m in ag_cfg.get("models", [])]
            if any(am in model_lower or model_lower in am for am in ag_models):
                return "antigravity", ag_cfg

        # 3. Heuristic matching across known provider ecosystems
        heuristic_map = [
            ("claude", "anthropic"),
            ("gpt", "openai"),
            ("o3", "openai"),
            ("o1", "openai"),
            ("deepseek", "deepseek"),
            ("gemini", "gemini"),
            ("grok", "xai"),
            ("groq", "groq"),
            ("mistral", "mistral"),
            ("codestral", "mistral"),
            ("command", "cohere"),
            ("sonar", "perplexity"),
            ("together", "together"),
            ("cerebras", "cerebras"),
            ("sambanova", "sambanova"),
            ("fireworks", "fireworks"),
            ("silicon", "siliconflow"),
            ("moonshot", "moonshot"),
            ("kimi", "moonshot"),
            ("glm", "zhipu"),
            ("minimax", "minimax"),
            ("qwen", "dashscope"),
            ("dashscope", "dashscope"),
            ("baichuan", "baichuan"),
            ("yi", "01ai"),
            ("venice", "venice"),
            ("opencode", "opencode"),
            ("ollama", "ollama"),
            ("vllm", "vllm"),
            ("lmstudio", "lmstudio"),
            ("llamacpp", "llamacpp"),
            ("localai", "localai"),
            ("openrouter", "openrouter")
        ]

        for token, p_name in heuristic_map:
            if token in model_lower:
                if p_name in providers:
                    return p_name, providers[p_name]

        # 4. Fallback to openrouter or first available configured provider
        if "openrouter" in providers:
            return "openrouter", providers["openrouter"]
        if providers:
            first = next(iter(providers))
            return first, providers[first]
        return None

    def test_provider(self, name: str) -> Tuple[bool, str, float]:
        """Test a provider by issuing a lightweight test query.

        Returns:
            Tuple[success: bool, message: str, latency_seconds: float]
        """
        providers = config.get("providers", {})
        p_data = providers.get(name)
        if not p_data:
            return False, f"Provider '{name}' belum dikonfigurasi", 0.0

        api_key = p_data.get("api_key", "").strip()
        base_url = p_data.get("base_url", "").rstrip("/")
        models = p_data.get("models", [])
        is_local = name in ["ollama", "vllm", "lmstudio", "llamacpp", "localai"]

        # 1. Antigravity Provider Special Testing
        if name == "antigravity":
            start_t = time.time()
            ag_token = oauth_manager.get_valid_antigravity_token()
            if not ag_token:
                return False, "Token Google Antigravity tidak ditemukan. Silakan login opsi [a]", 0.0

            url = "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist"
            headers = {
                "Authorization": f"Bearer {ag_token}",
                "Content-Type": "application/json",
                "User-Agent": "Antigravity/2.0"
            }
            try:
                resp = requests.post(url, headers=headers, json={}, timeout=15)
                latency = round(time.time() - start_t, 3)
                if resp.status_code == 200:
                    tier = resp.json().get("currentTier", {}).get("name", "Antigravity")
                    return True, f"OK ({tier})", latency
                return False, f"HTTP {resp.status_code}: {resp.text[:120]}", latency
            except Exception as e:
                latency = round(time.time() - start_t, 3)
                return False, f"Connection error: {str(e)[:120]}", latency

        # 2. Copilot Provider Special Testing
        if name == "copilot":
            start_t = time.time()
            cop_token = oauth_manager.get_valid_copilot_token()
            if not cop_token:
                return False, "Token Copilot tidak aktif. Silakan login kembali dengan opsi [g]", 0.0

            headers = {
                "Authorization": f"Bearer {cop_token}",
                "Editor-Version": "vscode/1.85.1",
                "Editor-Plugin-Version": "copilot/1.144.0",
                "User-Agent": "GithubCopilot/1.144.0",
                "Openai-Intent": "conversation-panel",
                "Content-Type": "application/json"
            }
            test_model = models[0] if models else "gpt-4o"
            url = "https://api.githubcopilot.com/chat/completions"
            payload = {
                "model": test_model,
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "ping"}]
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=20)
                latency = round(time.time() - start_t, 3)
                if resp.status_code in [200, 201]:
                    return True, f"OK Copilot ({test_model})", latency
                return False, f"HTTP {resp.status_code}: {resp.text[:120]}", latency
            except Exception as e:
                latency = round(time.time() - start_t, 3)
                return False, f"Connection error: {str(e)[:120]}", latency

        # 2. Check Key Requirement for Non-Local Providers
        if not is_local and (not api_key or api_key.startswith("YOUR_")):
            return False, "API key belum diatur atau masih template placeholder", 0.0

        test_model = models[0] if models else "gpt-3.5-turbo"
        start_t = time.time()

        try:
            # Handle Anthropic Messages format
            if name in ["anthropic", "claude-code"]:
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                url = f"{base_url}/messages"
                payload = {
                    "model": test_model,
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "ping"}]
                }
            else:
                # Standard OpenAI-compatible format
                headers = {
                    "Authorization": f"Bearer {api_key}" if api_key and api_key != "none" else "",
                    "Content-Type": "application/json"
                }
                url = f"{base_url}/chat/completions"
                payload = {
                    "model": test_model,
                    "max_tokens": 3,
                    "messages": [{"role": "user", "content": "ping"}]
                }

            timeout_sec = 25
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                # Automatic 1-time retry for cold-start queue delay on free/cloud models
                time.sleep(0.5)
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)

            latency = round(time.time() - start_t, 3)

            if resp.status_code in [200, 201]:
                return True, f"OK ({test_model})", latency
            else:
                return False, f"HTTP {resp.status_code}: {resp.text[:120]}", latency
        except Exception as e:
            latency = round(time.time() - start_t, 3)
            return False, f"Connection error: {str(e)[:120]}", latency

    def fetch_live_models(self, name: str) -> Tuple[bool, str, List[str]]:
        """Fetch real-time available models from upstream provider API."""
        providers = config.get("providers", {})
        p_data = providers.get(name, {})
        if not p_data:
            return False, f"Provider '{name}' tidak ditemukan di konfigurasi.", []

        api_key = p_data.get("api_key", "").strip()
        base_url = p_data.get("base_url", "").rstrip("/")

        # 1. Google Antigravity
        if name == "antigravity":
            ag_token = oauth_manager.get_valid_antigravity_token()
            if not ag_token:
                return False, "Token Google Antigravity tidak aktif.", []
            url = "https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels"
            headers = {
                "Authorization": f"Bearer {ag_token}",
                "Content-Type": "application/json",
                "User-Agent": "Antigravity/2.0"
            }
            try:
                resp = requests.post(url, headers=headers, json={}, timeout=10)
                if resp.status_code == 200:
                    raw_models = resp.json().get("models", {})
                    fetched = []
                    for m_id, info in raw_models.items():
                        if not m_id.startswith("tab_") and not m_id.startswith("chat_"):
                            fetched.append(m_id)
                    if fetched:
                        p_data["models"] = fetched
                        providers["antigravity"] = p_data
                        config.set("providers", providers, auto_save=True)
                        return True, f"Berhasil sinkronisasi {len(fetched)} model dari Google Antigravity!", fetched
                return False, f"HTTP {resp.status_code}: {resp.text[:120]}", []
            except Exception as e:
                return False, str(e), []

        # 2. Local Ollama
        if name == "ollama":
            try:
                resp = requests.get("http://localhost:11434/api/tags", timeout=3)
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    if models:
                        p_data["models"] = models
                        providers["ollama"] = p_data
                        config.set("providers", providers, auto_save=True)
                        return True, f"Berhasil membaca {len(models)} model dari Ollama lokal!", models
                return False, "Ollama tidak sedang berjalan di port 11434.", []
            except Exception as e:
                return False, str(e), []

        # 3. Standard OpenAI-compatible endpoints
        if not api_key and name not in ["vllm", "lmstudio", "llamacpp"]:
            return False, "API key belum diisi untuk provider ini.", []

        url = f"{base_url}/models"
        headers = {"Content-Type": "application/json"}
        if api_key and api_key != "none":
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                model_items = data.get("data", [])
                models = [m["id"] for m in model_items if isinstance(m, dict) and "id" in m]
                if models:
                    p_data["models"] = models
                    providers[name] = p_data
                    config.set("providers", providers, auto_save=True)
                    return True, f"Berhasil sinkronisasi {len(models)} model dari {name.upper()}!", models
            return False, f"HTTP {resp.status_code}: {resp.text[:120]}", []
        except Exception as e:
            return False, str(e), []

    def is_provider_configured(self, name: str) -> bool:
        """Check if a provider has active credentials or is a reachable local engine."""
        providers = config.get("providers", {})
        p_data = providers.get(name)
        if not p_data:
            return False

        if name == "antigravity":
            return bool(oauth_manager.get_valid_antigravity_token() or p_data.get("api_key"))
        if name == "copilot":
            return bool(oauth_manager.get_valid_copilot_token() or p_data.get("api_key") or p_data.get("copilot_token"))
        if name in ["claude-code", "claude"]:
            return bool(p_data.get("api_key") or p_data.get("session_token"))
        if name == "codex":
            return bool(p_data.get("api_key") or p_data.get("accessToken") or p_data.get("session_token"))
        if name == "cursor":
            return bool(p_data.get("api_key") or p_data.get("token"))
        if name in ["kilo", "cline", "iflow", "qwen-code", "gemini-cli", "kiro"]:
            return bool(p_data.get("api_key") and p_data.get("api_key") != "none")

        api_key = p_data.get("api_key", "").strip()
        is_local = name in ["ollama", "vllm", "lmstudio", "llamacpp", "localai"]
        if is_local:
            import socket
            base_url = p_data.get("base_url", "")
            port = 11434
            if ":11434" in base_url:
                port = 11434
            elif ":8000" in base_url:
                port = 8000
            elif ":1234" in base_url:
                port = 1234
            elif ":8080" in base_url:
                port = 8080
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.15):
                    return True
            except (OSError, ConnectionRefusedError):
                return False

        return bool(api_key and not api_key.startswith("YOUR_") and api_key != "none")

    def refresh_all_models(self) -> Dict[str, Tuple[bool, str, List[str]]]:
        """Synchronize models for all configured providers."""
        results: Dict[str, Tuple[bool, str, List[str]]] = {}
        providers = config.get("providers", {})
        for name in providers:
            results[name] = self.fetch_live_models(name)
        return results

    def test_all(self, only_configured: bool = True) -> Dict[str, Tuple[bool, str, float]]:
        """Run diagnostics on providers.
        
        Args:
            only_configured: If True, only tests providers that have valid credentials
                             or active reachable endpoints. Default True.
        """
        results: Dict[str, Tuple[bool, str, float]] = {}
        providers = config.get("providers", {})

        if only_configured:
            targets = [name for name in providers if self.is_provider_configured(name)]
            if not targets:
                active_p = config.get("active_provider")
                targets = [active_p] if active_p in providers else list(providers.keys())[:5]
        else:
            targets = list(providers.keys())

        for name in targets:
            results[name] = self.test_provider(name)
        return results


# Global provider manager instance
provider_manager = ProviderManager()
