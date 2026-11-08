"""Comprehensive 46+ Provider Catalog from 9Router & 9Router Pro with 2025/2026 Latest Frontier Models."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

PROVIDER_CATEGORIES: Dict[str, str] = {
    "all": "Semua Provider (46+ Provider)",
    "oauth": "🔑 Akun & Langganan (Antigravity, Copilot, Claude, Codex, Cursor, Kiro)",
    "frontier": "🏛️ Frontier Commercial (Anthropic, OpenAI, Gemini, DeepSeek, xAI, Mistral)",
    "fast": "⚡ Fast Inference (Groq, Cerebras, SambaNova, Together, Fireworks, SiliconFlow, Hyperbolic)",
    "apac": "🌏 APAC & China (Kimi, GLM, MiniMax, Qwen DashScope, Yi, Qianfan, Hunyuan, StepFun)",
    "cloud": "☁️ Enterprise Cloud (Azure OpenAI, AWS Bedrock, Google Vertex AI, Cloudflare)",
    "agg": "🌐 Aggregators & Free Tiers (OpenRouter, Venice, Gemini Free, OpenCode)",
    "local": "🦙 Local & Self-Hosted (Ollama, vLLM, LM Studio, llama.cpp, LocalAI)"
}

FULL_PROVIDER_CATALOG: List[Dict[str, Any]] = [
    # --- 1. OAUTH & SUBSCRIPTION TIERS (Zero Extra Cost - Frontier Models) ---
    {
        "id": "antigravity",
        "name": "Google Antigravity",
        "category": "oauth",
        "icon": "🌌",
        "auth_type": "oauth_session",
        "url": "https://cloudcode-pa.googleapis.com/v1internal",
        "models": [
            "claude-sonnet-4-6",
            "claude-opus-4-6-thinking",
            "gemini-3.8-flash-tiered",
            "gemini-3-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.1-flash-image",
            "gemini-2.5-pro",
            "gemini-2.5-flash-thinking",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-pro-exp",
            "gpt-oss-120b-medium"
        ],
        "description": "Akun Google Antigravity (Cloud Code Assist) otomatis dari ~/.gemini/antigravity-cli"
    },
    {
        "id": "copilot",
        "name": "GitHub Copilot",
        "category": "oauth",
        "icon": "🐙",
        "auth_type": "oauth_device",
        "url": "https://api.githubcopilot.com",
        "models": [
            "claude-3.7-sonnet",
            "claude-3.7-sonnet-thought",
            "claude-3.5-sonnet",
            "o3-mini",
            "o1",
            "o1-mini",
            "o1-preview",
            "gpt-4.5-preview",
            "gpt-4o",
            "gpt-4o-mini"
        ],
        "description": "Gunakan kuota langganan GitHub Copilot Anda untuk Claude 3.7 & GPT-4o tanpa bayar token"
    },
    {
        "id": "claude-code",
        "name": "Claude Code CLI Session",
        "category": "oauth",
        "icon": "🟣",
        "auth_type": "session_import",
        "url": "https://api.anthropic.com/v1",
        "models": [
            "claude-3-7-sonnet-20250219",
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-20241022",
            "claude-3-5-haiku-latest",
            "claude-3-opus-20240229",
            "claude-3-opus-latest"
        ],
        "description": "Import session Claude Code (~/.claude.json) atau paste OAuth token"
    },
    {
        "id": "codex",
        "name": "OpenAI Codex & ChatGPT Plus",
        "category": "oauth",
        "icon": "🟢",
        "auth_type": "session_import",
        "url": "https://chatgpt.com/backend-api",
        "models": [
            "o3-mini",
            "o3-mini-high",
            "o3-pro",
            "o1",
            "o1-preview",
            "gpt-4.5-preview",
            "chatgpt-4o-latest",
            "gpt-4o",
            "gpt-4o-mini"
        ],
        "description": "Session token ChatGPT Plus / OpenAI Codex untuk bypass bayar token API"
    },
    {
        "id": "cursor",
        "name": "Cursor Session",
        "category": "oauth",
        "icon": "⚡",
        "auth_type": "session_import",
        "url": "https://api.cursor.com/v1",
        "models": [
            "cursor-fast",
            "cursor-small",
            "claude-3.7-sonnet",
            "claude-3.7-sonnet-thinking",
            "claude-3.5-sonnet",
            "gpt-4o",
            "gpt-4o-mini",
            "o3-mini",
            "o1",
            "deepseek-r1",
            "deepseek-v3"
        ],
        "description": "Import auth token Cursor untuk akses model berkecepatan tinggi"
    },
    {
        "id": "kiro",
        "name": "Kiro AI Free Tier",
        "category": "oauth",
        "icon": "🎁",
        "auth_type": "api_key",
        "url": "https://api.kiro.ai/v1",
        "models": [
            "kiro-claude-3.7-sonnet",
            "kiro-claude-3.5-sonnet",
            "kiro-deepseek-r1",
            "kiro-glm-4",
            "kiro-llama-3.3"
        ],
        "description": "Platform Kiro AI dengan alokasi token gratis untuk model Claude & GLM"
    },

    # --- 2. FRONTIER COMMERCIAL PROVIDERS ---
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "category": "frontier",
        "icon": "🟣",
        "auth_type": "api_key",
        "url": "https://api.anthropic.com/v1",
        "models": [
            "claude-3-7-sonnet-20250219",
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-20241022",
            "claude-3-5-haiku-latest",
            "claude-3-opus-20240229",
            "claude-3-opus-latest"
        ],
        "description": "Frontier agentic model terbaik untuk coding mandiri & hybrid reasoning"
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "category": "frontier",
        "icon": "🟢",
        "auth_type": "api_key",
        "url": "https://api.openai.com/v1",
        "models": [
            "o3-mini",
            "o3-mini-high",
            "o3-pro",
            "o1",
            "o1-2024-12-17",
            "o1-preview",
            "o1-mini",
            "gpt-4.5-preview",
            "gpt-4.5-preview-2025-02-27",
            "chatgpt-4o-latest",
            "gpt-4o-2024-11-20",
            "gpt-4o",
            "gpt-4o-mini"
        ],
        "description": "Model OpenAI reasoning o3-mini & flagship GPT-4.5"
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "category": "frontier",
        "icon": "💎",
        "auth_type": "api_key",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-pro-exp-02-05",
            "gemini-2.0-pro-exp",
            "gemini-2.0-flash-thinking-exp-01-21",
            "gemini-2.0-flash-thinking-exp",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash-8b"
        ],
        "description": "Model 2M context window dengan inferensi super cepat"
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "category": "frontier",
        "icon": "🔵",
        "auth_type": "api_key",
        "url": "https://api.deepseek.com/v1",
        "models": [
            "deepseek-reasoner",
            "deepseek-chat",
            "deepseek-v4-pro",
            "deepseek-coder-v2"
        ],
        "description": "DeepSeek R1 (671B Full Reasoning) dan DeepSeek V3 (MoE) performa frontier"
    },
    {
        "id": "xai",
        "name": "xAI (Grok)",
        "category": "frontier",
        "icon": "✖️",
        "auth_type": "api_key",
        "url": "https://api.x.ai/v1",
        "models": [
            "grok-3",
            "grok-3-mini",
            "grok-2-1212",
            "grok-2-vision-1212",
            "grok-beta"
        ],
        "description": "Model xAI Grok 3 dengan akses data real-time & unconstrained reasoning"
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "category": "frontier",
        "icon": "🌪️",
        "auth_type": "api_key",
        "url": "https://api.mistral.ai/v1",
        "models": [
            "codestral-2501",
            "codestral-latest",
            "mistral-large-2411",
            "mistral-large-latest",
            "mistral-small-24b-instruct-2501",
            "mistral-small-latest",
            "pixtral-large-latest",
            "pixtral-12b",
            "ministral-8b-latest",
            "ministral-3b-latest"
        ],
        "description": "Codestral 2501 & Mistral Large 2411 model coding terdepan Eropa"
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "category": "frontier",
        "icon": "🌿",
        "auth_type": "api_key",
        "url": "https://api.cohere.com/v2",
        "models": [
            "command-r-plus-08-2024",
            "command-r-plus",
            "command-r7b-12-2024",
            "command-r"
        ],
        "description": "Command R+ enterprise agentic reasoning & tool use"
    },
    {
        "id": "perplexity",
        "name": "Perplexity AI",
        "category": "frontier",
        "icon": "🔍",
        "auth_type": "api_key",
        "url": "https://api.perplexity.ai",
        "models": [
            "sonar-deep-research",
            "sonar-reasoning-pro",
            "sonar-reasoning",
            "sonar-pro",
            "sonar"
        ],
        "description": "Online real-time web deep research augmented reasoning models"
    },

    # --- 3. FAST INFERENCE & LOW LATENCY ---
    {
        "id": "groq",
        "name": "Groq LPU",
        "category": "fast",
        "icon": "⚡",
        "auth_type": "api_key",
        "url": "https://api.groq.com/openai/v1",
        "models": [
            "deepseek-r1-distill-llama-70b",
            "deepseek-r1-distill-qwen-32b",
            "llama-3.3-70b-versatile",
            "llama-3.3-70b-specdec",
            "qwen-2.5-coder-32b",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "whisper-large-v3-turbo",
            "whisper-large-v3"
        ],
        "description": "Inference tercepat di dunia via Groq LPU (~500 tok/detik)"
    },
    {
        "id": "cerebras",
        "name": "Cerebras",
        "category": "fast",
        "icon": "🧠",
        "auth_type": "api_key",
        "url": "https://api.cerebras.ai/v1",
        "models": [
            "deepseek-r1-distill-llama-70b",
            "llama3.3-70b",
            "llama3.1-70b",
            "llama3.1-8b"
        ],
        "description": "Inference ultra-cepat hingga 2.000 tokens per detik"
    },
    {
        "id": "sambanova",
        "name": "SambaNova",
        "category": "fast",
        "icon": "🚀",
        "auth_type": "api_key",
        "url": "https://api.sambanova.ai/v1",
        "models": [
            "DeepSeek-R1",
            "DeepSeek-R1-Distill-Llama-70B",
            "Meta-Llama-3.3-70B-Instruct",
            "Meta-Llama-3.1-405B-Instruct",
            "Meta-Llama-3.1-70B-Instruct",
            "Qwen2.5-Coder-32B-Instruct",
            "Qwen2.5-72B-Instruct"
        ],
        "description": "Inference chip SN40L super cepat & hemat biaya"
    },
    {
        "id": "together",
        "name": "Together AI",
        "category": "fast",
        "icon": "🤝",
        "auth_type": "api_key",
        "url": "https://api.together.xyz/v1",
        "models": [
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-V3",
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
            "mistralai/Mistral-Small-24B-Instruct-2501"
        ],
        "description": "Open-source model cloud terpopuler dengan Llama 3.3 & DeepSeek R1"
    },
    {
        "id": "fireworks",
        "name": "Fireworks AI",
        "category": "fast",
        "icon": "🎆",
        "auth_type": "api_key",
        "url": "https://api.fireworks.ai/inference/v1",
        "models": [
            "accounts/fireworks/models/deepseek-r1",
            "accounts/fireworks/models/deepseek-v3",
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/qwen2p5-coder-32b-instruct",
            "accounts/fireworks/models/qwen2p5-72b-instruct"
        ],
        "description": "Inference engine teroptimasi dengan model DeepSeek R1 & Llama"
    },
    {
        "id": "siliconflow",
        "name": "SiliconFlow (SiliconCloud)",
        "category": "fast",
        "icon": "🌊",
        "auth_type": "api_key",
        "url": "https://api.siliconflow.cn/v1",
        "models": [
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct",
            "meta-llama/Llama-3.3-70B-Instruct",
            "TeleAI/TeleChat2"
        ],
        "description": "Penyedia model open-source terbesar di Asia dengan harga ekonomis"
    },
    {
        "id": "deepinfra",
        "name": "DeepInfra",
        "category": "fast",
        "icon": "🏗️",
        "auth_type": "api_key",
        "url": "https://api.deepinfra.com/v1/openai",
        "models": [
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-V3",
            "meta-llama/Llama-3.3-70B-Instruct",
            "meta-llama/Meta-Llama-3.1-405B-Instruct",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct"
        ],
        "description": "Inference serverless bayar per token tanpa server idle"
    },
    {
        "id": "novita",
        "name": "Novita AI",
        "category": "fast",
        "icon": "⭐",
        "auth_type": "api_key",
        "url": "https://api.novita.ai/v3/openai",
        "models": [
            "deepseek/deepseek-r1",
            "deepseek/deepseek-v3",
            "meta-llama/llama-3.3-70b-instruct",
            "qwen/qwen-2.5-coder-32b-instruct"
        ],
        "description": "GPU Cloud inference performa tinggi"
    },
    {
        "id": "hyperbolic",
        "name": "Hyperbolic",
        "category": "fast",
        "icon": "⚡",
        "auth_type": "api_key",
        "url": "https://api.hyperbolic.xyz/v1",
        "models": [
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-V3",
            "meta-llama/Llama-3.3-70B-Instruct",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct"
        ],
        "description": "Open-access AI computing platform dengan GPU terdesentralisasi"
    },

    # --- 4. APAC & CHINESE MODELS ---
    {
        "id": "moonshot",
        "name": "Moonshot AI (Kimi)",
        "category": "apac",
        "icon": "🌙",
        "auth_type": "api_key",
        "url": "https://api.moonshot.cn/v1",
        "models": [
            "kimi-k1.5",
            "moonshot-v1-128k",
            "moonshot-v1-32k",
            "moonshot-v1-8k",
            "moonshot-v1-auto"
        ],
        "description": "Kimi AI terkenal dengan pemrosesan dokumen panjang & long context"
    },
    {
        "id": "zhipu",
        "name": "Zhipu AI (GLM)",
        "category": "apac",
        "icon": "🏮",
        "auth_type": "api_key",
        "url": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            "glm-4-plus",
            "glm-4-0520",
            "glm-4-flash",
            "glm-4-flashx",
            "glm-4-air",
            "glm-4-airx",
            "glm-4-long",
            "glm-4-voice"
        ],
        "description": "GLM 4 series dari Tsinghua / Zhipu AI"
    },
    {
        "id": "minimax",
        "name": "MiniMax",
        "category": "apac",
        "icon": "🎪",
        "auth_type": "api_key",
        "url": "https://api.minimax.chat/v1",
        "models": [
            "abab6.5s-chat",
            "abab6.5t-chat",
            "abab6.5-chat",
            "MiniMax-Text-01"
        ],
        "description": "Model abab series dengan kemampuan multimodal kuat"
    },
    {
        "id": "dashscope",
        "name": "Alibaba DashScope (Qwen)",
        "category": "apac",
        "icon": "☁️",
        "auth_type": "api_key",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": [
            "qwen-max-latest",
            "qwen-max",
            "qwen-plus-latest",
            "qwen-plus",
            "qwen-turbo-latest",
            "qwen2.5-coder-32b-instruct",
            "qwen2.5-coder-14b-instruct",
            "qwen2.5-coder-7b-instruct",
            "qwen2.5-72b-instruct",
            "qvq-72b-preview"
        ],
        "description": "Model resmi Alibaba Cloud Qwen 2.5 Coder & Max"
    },
    {
        "id": "baichuan",
        "name": "Baichuan AI",
        "category": "apac",
        "icon": "🏔️",
        "auth_type": "api_key",
        "url": "https://api.baichuan-ai.com/v1",
        "models": [
            "Baichuan4",
            "Baichuan3-Turbo",
            "Baichuan3-Turbo-128k",
            "Baichuan2-Turbo"
        ],
        "description": "Model bahasa Mandarin & bilingual performa tinggi"
    },
    {
        "id": "01ai",
        "name": "01.AI (Yi)",
        "category": "apac",
        "icon": "🎯",
        "auth_type": "api_key",
        "url": "https://api.01.ai/v1",
        "models": [
            "yi-lightning",
            "yi-large",
            "yi-large-turbo",
            "yi-medium",
            "yi-spark"
        ],
        "description": "Model Yi dari Dr. Kai-Fu Lee dengan kecepatan tinggi"
    },
    {
        "id": "qianfan",
        "name": "Baidu Qianfan (ERNIE)",
        "category": "apac",
        "icon": "🐻",
        "auth_type": "api_key",
        "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
        "models": [
            "ernie-4.0-turbo-8k",
            "ernie-4.0-8k-latest",
            "ernie-4.0-8k",
            "ernie-3.5-8k",
            "ernie-speed-128k"
        ],
        "description": "Model Baidu ERNIE Bot flagship"
    },
    {
        "id": "hunyuan",
        "name": "Tencent Hunyuan",
        "category": "apac",
        "icon": "🐧",
        "auth_type": "api_key",
        "url": "https://api.hunyuan.cloud.tencent.com/v1",
        "models": [
            "hunyuan-pro",
            "hunyuan-standard",
            "hunyuan-lite",
            "hunyuan-code",
            "hunyuan-turbo"
        ],
        "description": "Model Tencent Hunyuan untuk pemrosesan teks & kode"
    },
    {
        "id": "stepfun",
        "name": "StepFun (Jieyue)",
        "category": "apac",
        "icon": "🪜",
        "auth_type": "api_key",
        "url": "https://api.stepfun.com/v1",
        "models": [
            "step-2-16k",
            "step-1-128k",
            "step-1-32k",
            "step-1v-8k",
            "step-1v-32k"
        ],
        "description": "Model StepFun multimodal & general reasoning"
    },

    # --- 5. ENTERPRISE CLOUD PLATFORMS ---
    {
        "id": "azure",
        "name": "Azure OpenAI Service",
        "category": "cloud",
        "icon": "🔷",
        "auth_type": "api_key",
        "url": "https://your-resource.openai.azure.com",
        "models": [
            "o3-mini",
            "o1",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo"
        ],
        "description": "Deployment Microsoft Azure OpenAI enterprise dengan SLA"
    },
    {
        "id": "bedrock",
        "name": "AWS Bedrock",
        "category": "cloud",
        "icon": "🟧",
        "auth_type": "api_key",
        "url": "https://bedrock-runtime.us-east-1.amazonaws.com",
        "models": [
            "anthropic.claude-3-7-sonnet-20250219-v1:0",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-haiku-20241022-v1:0",
            "meta.llama3-3-70b-instruct-v1:0",
            "amazon.nova-pro-v1:0",
            "amazon.nova-lite-v1:0"
        ],
        "description": "Amazon Web Services Bedrock foundation models"
    },
    {
        "id": "vertex",
        "name": "Google Cloud Vertex AI",
        "category": "cloud",
        "icon": "🌈",
        "auth_type": "api_key",
        "url": "https://us-central1-aiplatform.googleapis.com/v1",
        "models": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-thinking-exp",
            "gemini-2.0-pro-exp",
            "claude-3-7-sonnet@20250219",
            "claude-3-5-sonnet@20241022",
            "claude-3-5-haiku@20241022"
        ],
        "description": "Google Cloud Vertex AI enterprise managed inference"
    },
    {
        "id": "cloudflare",
        "name": "Cloudflare Workers AI",
        "category": "cloud",
        "icon": "🟧",
        "auth_type": "api_key",
        "url": "https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1",
        "models": [
            "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
            "@cf/meta/llama-3.3-70b-instruct",
            "@cf/meta/llama-3.1-70b-instruct",
            "@cf/meta/llama-3.1-8b-instruct",
            "@cf/qwen/qwen2.5-coder-32b-instruct"
        ],
        "description": "Edge AI inference di 300+ kota seluruh dunia via Cloudflare"
    },
    {
        "id": "ai21",
        "name": "AI21 Labs",
        "category": "cloud",
        "icon": "🧬",
        "auth_type": "api_key",
        "url": "https://api.ai21.com/studio/v1",
        "models": [
            "jamba-1.5-large",
            "jamba-1.5-mini"
        ],
        "description": "SSM-Transformer hybrid architecture (Jamba models)"
    },

    # --- 6. AGGREGATORS & FREE TIERS ---
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "category": "agg",
        "icon": "🌐",
        "auth_type": "api_key",
        "url": "https://openrouter.ai/api/v1",
        "models": [
            "deepseek/deepseek-r1",
            "deepseek/deepseek-v3",
            "anthropic/claude-3.7-sonnet",
            "anthropic/claude-3.7-sonnet:thinking",
            "anthropic/claude-3.5-sonnet",
            "openai/o3-mini",
            "openai/o3-mini-high",
            "openai/o1",
            "openai/gpt-4.5-preview",
            "openai/gpt-4o-2024-11-20",
            "google/gemini-2.0-flash-001",
            "google/gemini-2.0-pro-exp-02-05:free",
            "meta-llama/llama-3.3-70b-instruct",
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
            "qwen/qwen-2.5-coder-32b-instruct"
        ],
        "description": "Akses ke ratusan model dalam satu kunci API dengan opsi tier gratis"
    },
    {
        "id": "venice",
        "name": "Venice AI",
        "category": "agg",
        "icon": "🎭",
        "auth_type": "api_key",
        "url": "https://api.venice.ai/api/v1",
        "models": [
            "llama-3.3-70b",
            "deepseek-r1-llama-70b",
            "qwen-2.5-coder-32b",
            "mistral-large"
        ],
        "description": "Model uncensored dengan privasi total tanpa logging riwayat"
    },
    {
        "id": "opencode",
        "name": "OpenCode Free Tier",
        "category": "agg",
        "icon": "🎁",
        "auth_type": "api_key",
        "url": "https://api.opencode.ai/v1",
        "models": [
            "opencode-glm-4-free",
            "opencode-llama-free",
            "opencode-deepseek-r1-free",
            "opencode-qwen2.5-free"
        ],
        "description": "Tier gratis khusus coding & tools"
    },
    {
        "id": "gemini-free",
        "name": "Google AI Studio (Free Tier)",
        "category": "agg",
        "icon": "🆓",
        "auth_type": "api_key",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-thinking-exp",
            "gemini-2.0-pro-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ],
        "description": "API gratis dari Google AI Studio hingga 15 RPM tanpa biaya"
    },

    # --- 7. LOCAL & SELF-HOSTED ENGINES ---
    {
        "id": "ollama",
        "name": "Ollama (Lokal)",
        "category": "local",
        "icon": "🦙",
        "auth_type": "none",
        "url": "http://localhost:11434/v1",
        "models": [
            "deepseek-r1:671b",
            "deepseek-r1:70b",
            "deepseek-r1:32b",
            "deepseek-r1:14b",
            "deepseek-r1:8b",
            "deepseek-r1:1.5b",
            "qwen2.5-coder:32b",
            "qwen2.5-coder:14b",
            "qwen2.5-coder:7b",
            "qwen2.5-coder:1.5b",
            "llama3.3:70b",
            "llama3.2:3b",
            "llama3.2:1b",
            "mistral-small:24b",
            "codellama:70b",
            "starcoder2:15b"
        ],
        "description": "Engine LLM lokal offline paling populer, gratis 100% tanpa internet"
    },
    {
        "id": "vllm",
        "name": "vLLM Server",
        "category": "local",
        "icon": "⚡",
        "auth_type": "none",
        "url": "http://localhost:8000/v1",
        "models": [
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "meta-llama/Llama-3.3-70B-Instruct"
        ],
        "description": "Engine throughput tinggi untuk GPU lokal / server mandiri"
    },
    {
        "id": "lmstudio",
        "name": "LM Studio (Lokal)",
        "category": "local",
        "icon": "🧪",
        "auth_type": "none",
        "url": "http://localhost:1234/v1",
        "models": [
            "deepseek-r1-distill-qwen-14b",
            "deepseek-r1-distill-llama-8b",
            "qwen2.5-coder-32b-instruct",
            "qwen2.5-coder-7b-instruct",
            "llama-3.3-70b-instruct",
            "meta-llama-3.1-8b-instruct"
        ],
        "description": "GUI desktop lokal LM Studio dengan local server endpoint"
    },
    {
        "id": "llamacpp",
        "name": "llama.cpp / llama-server",
        "category": "local",
        "icon": "🦙",
        "auth_type": "none",
        "url": "http://localhost:8080/v1",
        "models": [
            "DeepSeek-R1-Distill-Qwen-14B-GGUF",
            "DeepSeek-R1-Distill-Qwen-32B-GGUF",
            "Qwen2.5-Coder-32B-Instruct-GGUF",
            "Qwen2.5-Coder-7B-Instruct-GGUF",
            "Llama-3.3-70B-Instruct-GGUF"
        ],
        "description": "C++ native CPU/GPU inference server"
    },
    {
        "id": "localai",
        "name": "LocalAI",
        "category": "local",
        "icon": "🤖",
        "auth_type": "none",
        "url": "http://localhost:8080/v1",
        "models": [
            "deepseek-r1-distill-qwen-7b",
            "qwen2.5-coder-7b",
            "llama-3.2-3b",
            "phi-4"
        ],
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
