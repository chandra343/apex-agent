"""Comprehensive 35+ Provider Catalog from 9Router & 9Router Pro."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

PROVIDER_CATEGORIES: Dict[str, str] = {
    "all": "Semua Provider (35+ Provider)",
    "oauth": "🔑 Akun & Langganan (GitHub Copilot, Claude Code, Cursor)",
    "frontier": "🏛️ Frontier Commercial (Anthropic, OpenAI, Gemini, DeepSeek, xAI, Mistral)",
    "fast": "⚡ Fast Inference (Groq, Cerebras, SambaNova, Together, Fireworks, SiliconFlow)",
    "apac": "🌏 APAC & China (Kimi/Moonshot, GLM/Zhipu, MiniMax, Qwen DashScope, Yi)",
    "agg": "🌐 Aggregators & Free Tiers (OpenRouter, Venice, Gemini Free, OpenCode)",
    "local": "🦙 Local & Self-Hosted (Ollama, vLLM, LM Studio, llama.cpp, LocalAI)"
}

FULL_PROVIDER_CATALOG: List[Dict[str, Any]] = [
    # --- 1. OAUTH & SUBSCRIPTION TIERS (Zero Extra Cost) ---
    {
        "id": "copilot",
        "name": "GitHub Copilot",
        "category": "oauth",
        "icon": "🐙",
        "auth_type": "oauth_device",
        "url": "https://api.githubcopilot.com",
        "models": ["claude-3.7-sonnet", "claude-3.5-sonnet", "gpt-4o", "o3-mini", "o1"],
        "description": "Gunakan kuota langganan GitHub Copilot Anda untuk Claude 3.7 & GPT-4o tanpa bayar token"
    },
    {
        "id": "claude-code",
        "name": "Claude Code CLI Session",
        "category": "oauth",
        "icon": "🟣",
        "auth_type": "session_import",
        "url": "https://api.anthropic.com/v1",
        "models": ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
        "description": "Import session Claude Code (~/.claude.json) atau paste OAuth token"
    },
    {
        "id": "cursor",
        "name": "Cursor Session",
        "category": "oauth",
        "icon": "⚡",
        "auth_type": "session_import",
        "url": "https://api.cursor.com/v1",
        "models": ["cursor-fast", "claude-3.5-sonnet", "gpt-4o"],
        "description": "Import auth token Cursor untuk akses model berkecepatan tinggi"
    },

    # --- 2. FRONTIER COMMERCIAL PROVIDERS ---
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "category": "frontier",
        "icon": "🟣",
        "auth_type": "api_key",
        "url": "https://api.anthropic.com/v1",
        "models": ["claude-3-7-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"],
        "description": "Frontier agentic model terbaik untuk coding mandiri"
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "category": "frontier",
        "icon": "🟢",
        "auth_type": "api_key",
        "url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1"],
        "description": "Model OpenAI flagship GPT-4o & reasoning model o-series"
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "category": "frontier",
        "icon": "💎",
        "auth_type": "api_key",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-2.0-flash", "gemini-2.0-pro-exp", "gemini-1.5-pro"],
        "description": "Model 2M context window dengan inferensi super cepat"
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "category": "frontier",
        "icon": "🔵",
        "auth_type": "api_key",
        "url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "description": "DeepSeek V3 dan DeepSeek R1 reasoning performa tinggi & murah"
    },
    {
        "id": "xai",
        "name": "xAI (Grok)",
        "category": "frontier",
        "icon": "✖️",
        "auth_type": "api_key",
        "url": "https://api.x.ai/v1",
        "models": ["grok-2-1212", "grok-2-vision-1212", "grok-beta"],
        "description": "Model xAI Grok dengan akses real-time data & unconstrained reasoning"
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "category": "frontier",
        "icon": "🌪️",
        "auth_type": "api_key",
        "url": "https://api.mistral.ai/v1",
        "models": ["mistral-large-latest", "codestral-latest", "mistral-small-latest"],
        "description": "Codestral & Mistral Large model Eropa performa tinggi"
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "category": "frontier",
        "icon": "🌿",
        "auth_type": "api_key",
        "url": "https://api.cohere.com/v2",
        "models": ["command-r-plus-08-2024", "command-r-08-2024"],
        "description": "Command R+ enterprise agentic reasoning & tool use"
    },
    {
        "id": "perplexity",
        "name": "Perplexity AI",
        "category": "frontier",
        "icon": "🔍",
        "auth_type": "api_key",
        "url": "https://api.perplexity.ai",
        "models": ["sonar-reasoning-pro", "sonar-pro", "sonar"],
        "description": "Online real-time web search augmented reasoning models"
    },

    # --- 3. FAST INFERENCE & LOW LATENCY ---
    {
        "id": "groq",
        "name": "Groq LPU",
        "category": "fast",
        "icon": "⚡",
        "auth_type": "api_key",
        "url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "whisper-large-v3", "llama-3.1-8b-instant"],
        "description": "Inference tercepat di dunia via Groq LPU (~500 tok/detik)"
    },
    {
        "id": "cerebras",
        "name": "Cerebras",
        "category": "fast",
        "icon": "🧠",
        "auth_type": "api_key",
        "url": "https://api.cerebras.ai/v1",
        "models": ["llama3.3-70b", "llama3.1-8b"],
        "description": "Inference ultra-cepat hingga 2.000 tokens per detik"
    },
    {
        "id": "sambanova",
        "name": "SambaNova",
        "category": "fast",
        "icon": "🚀",
        "auth_type": "api_key",
        "url": "https://api.sambanova.ai/v1",
        "models": ["Meta-Llama-3.3-70B-Instruct", "Qwen2.5-Coder-32B-Instruct"],
        "description": "Inference chip SN40L super cepat & hemat biaya"
    },
    {
        "id": "together",
        "name": "Together AI",
        "category": "fast",
        "icon": "🤝",
        "auth_type": "api_key",
        "url": "https://api.together.xyz/v1",
        "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "Qwen/Qwen2.5-Coder-32B-Instruct"],
        "description": "Open-source model cloud terpopuler"
    },
    {
        "id": "fireworks",
        "name": "Fireworks AI",
        "category": "fast",
        "icon": "🎆",
        "auth_type": "api_key",
        "url": "https://api.fireworks.ai/inference/v1",
        "models": ["accounts/fireworks/models/deepseek-r1", "accounts/fireworks/models/llama-v3p3-70b-instruct"],
        "description": "Inference engine teroptimasi dengan model DeepSeek R1 & Llama"
    },
    {
        "id": "siliconflow",
        "name": "SiliconFlow (SiliconCloud)",
        "category": "fast",
        "icon": "🌊",
        "auth_type": "api_key",
        "url": "https://api.siliconflow.cn/v1",
        "models": ["deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1", "Qwen/Qwen2.5-Coder-32B-Instruct"],
        "description": "Penyedia model open-source terbesar di Asia dengan harga ekonomis"
    },
    {
        "id": "deepinfra",
        "name": "DeepInfra",
        "category": "fast",
        "icon": "🏗️",
        "auth_type": "api_key",
        "url": "https://api.deepinfra.com/v1/openai",
        "models": ["meta-llama/Llama-3.3-70B-Instruct", "deepseek-ai/DeepSeek-R1"],
        "description": "Inference serverless bayar per token tanpa server idle"
    },
    {
        "id": "novita",
        "name": "Novita AI",
        "category": "fast",
        "icon": "⭐",
        "auth_type": "api_key",
        "url": "https://api.novita.ai/v3/openai",
        "models": ["deepseek/deepseek-r1", "meta-llama/llama-3.3-70b-instruct"],
        "description": "GPU Cloud inference performa tinggi"
    },

    # --- 4. APAC & CHINESE MODELS ---
    {
        "id": "moonshot",
        "name": "Moonshot AI (Kimi)",
        "category": "apac",
        "icon": "🌙",
        "auth_type": "api_key",
        "url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-128k", "moonshot-v1-32k"],
        "description": "Kimi AI terkenal dengan pemrosesan dokumen panjang & long context"
    },
    {
        "id": "zhipu",
        "name": "Zhipu AI (GLM)",
        "category": "apac",
        "icon": "🏮",
        "auth_type": "api_key",
        "url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4-flash", "glm-4-air"],
        "description": "GLM 4 series dari Tsinghua / Zhipu AI"
    },
    {
        "id": "minimax",
        "name": "MiniMax",
        "category": "apac",
        "icon": "🎪",
        "auth_type": "api_key",
        "url": "https://api.minimax.chat/v1",
        "models": ["abab6.5s-chat", "abab6.5t-chat"],
        "description": "Model abab series dengan kemampuan multimodal kuat"
    },
    {
        "id": "dashscope",
        "name": "Alibaba DashScope (Qwen)",
        "category": "apac",
        "icon": "☁️",
        "auth_type": "api_key",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-max", "qwen-plus", "qwen-coder-plus"],
        "description": "Model resmi Alibaba Cloud Qwen 2.5 Coder & Max"
    },
    {
        "id": "baichuan",
        "name": "Baichuan AI",
        "category": "apac",
        "icon": "🏔️",
        "auth_type": "api_key",
        "url": "https://api.baichuan-ai.com/v1",
        "models": ["Baichuan4", "Baichuan3-Turbo"],
        "description": "Model bahasa Mandarin & bilingual performa tinggi"
    },
    {
        "id": "01ai",
        "name": "01.AI (Yi)",
        "category": "apac",
        "icon": "🎯",
        "auth_type": "api_key",
        "url": "https://api.01.ai/v1",
        "models": ["yi-lightning", "yi-large"],
        "description": "Model Yi dari Dr. Kai-Fu Lee dengan kecepatan tinggi"
    },

    # --- 5. AGGREGATORS & FREE TIERS ---
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "category": "agg",
        "icon": "🌐",
        "auth_type": "api_key",
        "url": "https://openrouter.ai/api/v1",
        "models": ["deepseek/deepseek-r1:free", "meta-llama/llama-3.3-70b-instruct:free"],
        "description": "Akses ke ratusan model dalam satu kunci API dengan opsi tier gratis"
    },
    {
        "id": "venice",
        "name": "Venice AI",
        "category": "agg",
        "icon": "🎭",
        "auth_type": "api_key",
        "url": "https://api.venice.ai/api/v1",
        "models": ["llama-3.3-70b", "deepseek-r1-llama-70b"],
        "description": "Model uncensored dengan privasi total tanpa logging riwayat"
    },
    {
        "id": "opencode",
        "name": "OpenCode Free Tier",
        "category": "agg",
        "icon": "🎁",
        "auth_type": "api_key",
        "url": "https://api.opencode.ai/v1",
        "models": ["opencode-glm-4-free", "opencode-llama-free"],
        "description": "Tier gratis khusus coding & tools"
    },
    {
        "id": "gemini-free",
        "name": "Google AI Studio (Free Tier)",
        "category": "agg",
        "icon": "🆓",
        "auth_type": "api_key",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-2.0-flash", "gemini-1.5-flash"],
        "description": "API gratis dari Google AI Studio hingga 15 RPM tanpa biaya"
    },

    # --- 6. LOCAL & SELF-HOSTED ENGINES ---
    {
        "id": "ollama",
        "name": "Ollama (Lokal)",
        "category": "local",
        "icon": "🦙",
        "auth_type": "none",
        "url": "http://localhost:11434/v1",
        "models": ["qwen2.5-coder:7b", "llama3.2:3b", "deepseek-r1:8b"],
        "description": "Engine LLM lokal offline paling populer, gratis 100% tanpa internet"
    },
    {
        "id": "vllm",
        "name": "vLLM Server",
        "category": "local",
        "icon": "⚡",
        "auth_type": "none",
        "url": "http://localhost:8000/v1",
        "models": ["vllm-model"],
        "description": "Engine throughput tinggi untuk GPU lokal / server mandiri"
    },
    {
        "id": "lmstudio",
        "name": "LM Studio (Lokal)",
        "category": "local",
        "icon": "🧪",
        "auth_type": "none",
        "url": "http://localhost:1234/v1",
        "models": ["local-model"],
        "description": "GUI desktop lokal LM Studio dengan local server endpoint"
    },
    {
        "id": "llamacpp",
        "name": "llama.cpp / llama-server",
        "category": "local",
        "icon": "🦙",
        "auth_type": "none",
        "url": "http://localhost:8080/v1",
        "models": ["gguf-model"],
        "description": "C++ native CPU/GPU inference server"
    },
    {
        "id": "localai",
        "name": "LocalAI",
        "category": "local",
        "icon": "🤖",
        "auth_type": "none",
        "url": "http://localhost:8080/v1",
        "models": ["local-model"],
        "description": "Drop-in replacement OpenAI REST API untuk model lokal"
    }
]


def get_providers_by_category(category: str = "all") -> List[Dict[str, Any]]:
    """Return filtered providers based on category ID."""
    if not category or category == "all":
        return list(FULL_PROVIDER_CATALOG)
    return [p for p in FULL_PROVIDER_CATALOG if p.get("category") == category]


def find_catalog_entry(provider_id: str) -> Optional[Dict[str, Any]]:
    """Find a provider catalog entry by ID."""
    p_id = provider_id.lower()
    for p in FULL_PROVIDER_CATALOG:
        if p["id"].lower() == p_id:
            return dict(p)
    return None
