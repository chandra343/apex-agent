"""Incremental Provider Manager with live Hot-Reloading and Test-All diagnostics."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from apex.config import config
from apex.router.key_pool import key_pool


class ProviderManager:
    """Manages active AI providers, endpoints, key pools, and testing."""

    def __init__(self) -> None:
        self.sync_with_config()

    def sync_with_config(self) -> None:
        """Register all configured provider keys into the key pool."""
        providers = config.get("providers", {})
        for name, p_data in providers.items():
            key = p_data.get("api_key", "")
            if key and key != "YOUR_ANTHROPIC_API_KEY" and key != "YOUR_OPENAI_API_KEY":
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
        key_pool.set_keys(name, api_key)

    def remove_provider(self, name: str) -> bool:
        """Remove a provider from configuration."""
        providers = config.get("providers", {})
        if name in providers:
            del providers[name]
            config.set("providers", providers, auto_save=True)
            return True
        return False

    def get_provider_for_model(self, model_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find the matching provider configuration for a given model."""
        providers = config.get("providers", {})
        model_lower = model_name.lower()

        # 1. Exact match in model list
        for name, p_data in providers.items():
            models = [m.lower() for m in p_data.get("models", [])]
            if model_lower in models:
                return name, p_data

        # 2. Heuristic prefix match
        if "claude" in model_lower:
            return "anthropic", providers.get("anthropic", {})
        if "gpt" in model_lower or "o3" in model_lower or "o1" in model_lower:
            return "openai", providers.get("openai", {})
        if "deepseek" in model_lower:
            return "deepseek", providers.get("deepseek", {})
        if "groq" in model_lower or "llama" in model_lower:
            return "groq", providers.get("groq", {})
        if "gemini" in model_lower:
            return "google", providers.get("google", {})

        # Default fallback to openrouter or first available
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
            return False, f"Provider '{name}' not found in configuration", 0.0

        api_key = p_data.get("api_key", "").strip()
        base_url = p_data.get("base_url", "").rstrip("/")
        models = p_data.get("models", [])

        if not api_key or "YOUR_" in api_key:
            return False, "API key is not configured or still placeholder", 0.0

        test_model = models[0] if models else "gpt-3.5-turbo"
        start_t = time.time()

        try:
            # Standard OpenAI-compatible test request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            if name == "anthropic":
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

    def test_all(self) -> Dict[str, Tuple[bool, str, float]]:
        """Run diagnostics on all configured providers concurrently."""
        results: Dict[str, Tuple[bool, str, float]] = {}
        providers = config.get("providers", {})
        for name in providers:
            results[name] = self.test_provider(name)
        return results


# Global provider manager instance
provider_manager = ProviderManager()
