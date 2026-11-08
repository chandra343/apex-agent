"""Token counter, rate limit tracker (RPM/TPM), and cost accounting ledger."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List
from apex.config import DATA_DIR

LEDGER_FILE = DATA_DIR / "ledger.json"

# Approximate pricing per 1M tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "claude-3-7-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku": {"input": 0.8, "output": 4.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "o3-mini": {"input": 1.1, "output": 4.4},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "llama-3.3-70b": {"input": 0.59, "output": 0.79},
}


class TokenLedger:
    """Records token usage, costs, and sliding window request rates."""

    def __init__(self) -> None:
        self.stats: Dict[str, Any] = {
            "total_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cached_tokens": 0,
            "estimated_cost_usd": 0.0,
            "models": {}
        }
        self._sliding_requests: List[float] = []
        self._sliding_tokens: List[tuple[float, int]] = []
        self._load()

    def _load(self) -> None:
        if LEDGER_FILE.exists():
            try:
                with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                    self.stats = json.load(f)
            except Exception:
                pass

    def _save(self) -> None:
        try:
            with open(LEDGER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass

    def record_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0
    ) -> float:
        """Record a completed API turn, compute cost, and update sliding metrics."""
        now = time.time()
        total_tokens = prompt_tokens + completion_tokens

        # 1. Update sliding window (60s)
        self._sliding_requests.append(now)
        self._sliding_tokens.append((now, total_tokens))
        self._prune_sliding(now)

        # 2. Compute cost
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        # 3. Update totals
        self.stats["total_requests"] += 1
        self.stats["total_prompt_tokens"] += prompt_tokens
        self.stats["total_completion_tokens"] += completion_tokens
        self.stats["total_cached_tokens"] += cached_tokens
        self.stats["estimated_cost_usd"] += cost

        # 4. Update per-model stats
        if model not in self.stats["models"]:
            self.stats["models"][model] = {
                "requests": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0
            }
        m_stat = self.stats["models"][model]
        m_stat["requests"] += 1
        m_stat["prompt_tokens"] += prompt_tokens
        m_stat["completion_tokens"] += completion_tokens
        m_stat["cost_usd"] += cost

        self._save()
        return cost

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = None
        for key, p in MODEL_PRICING.items():
            if key in model.lower():
                pricing = p
                break

        if not pricing:
            # Default fallback pricing (similar to standard cheap tier)
            pricing = {"input": 0.5, "output": 1.5}

        cost_in = (prompt_tokens / 1_000_000.0) * pricing["input"]
        cost_out = (completion_tokens / 1_000_000.0) * pricing["output"]
        return round(cost_in + cost_out, 6)

    def _prune_sliding(self, now: float) -> None:
        cutoff = now - 60.0
        self._sliding_requests = [t for t in self._sliding_requests if t > cutoff]
        self._sliding_tokens = [(t, n) for t, n in self._sliding_tokens if t > cutoff]

    @property
    def current_rpm(self) -> int:
        """Current requests per minute."""
        self._prune_sliding(time.time())
        return len(self._sliding_requests)

    @property
    def current_tpm(self) -> int:
        """Current tokens per minute."""
        self._prune_sliding(time.time())
        return sum(n for _, n in self._sliding_tokens)

    def get_summary_text(self) -> str:
        """Generate human-readable summary of usage and cost."""
        return (
            f"📊 **Usage Summary**\n"
            f"• Requests: {self.stats['total_requests']} (Current RPM: {self.current_rpm})\n"
            f"• Tokens: {self.stats['total_prompt_tokens'] + self.stats['total_completion_tokens']:,} "
            f"(Prompt: {self.stats['total_prompt_tokens']:,}, Completion: {self.stats['total_completion_tokens']:,})\n"
            f"• Estimated Cost: ${self.stats['estimated_cost_usd']:.4f} USD\n"
            f"• Current TPM: {self.current_tpm:,} tokens/min"
        )


# Global ledger instance
token_ledger = TokenLedger()
