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
            del providers[name]
            config.set("providers", providers, auto_save=True)
            return True
        return False

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
                resp = requests.post(url, headers=headers, json={}, timeout=8)
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
                resp = requests.post(url, headers=headers, json=payload, timeout=12)
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
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "ping"}]
                }

            resp = requests.post(url, headers=headers, json=payload, timeout=8)
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
            resp = requests.get(url, headers=headers, timeout=8)
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

    def refresh_all_models(self) -> Dict[str, Tuple[bool, str, List[str]]]:
        """Synchronize models for all configured providers."""
        results: Dict[str, Tuple[bool, str, List[str]]] = {}
        providers = config.get("providers", {})
        for name in providers:
            results[name] = self.fetch_live_models(name)
        return results

    def test_all(self) -> Dict[str, Tuple[bool, str, float]]:
        """Run diagnostics on all configured providers concurrently."""
        results: Dict[str, Tuple[bool, str, float]] = {}
        providers = config.get("providers", {})
        for name in providers:
            results[name] = self.test_provider(name)
        return results


# Global provider manager instance
provider_manager = ProviderManager()
