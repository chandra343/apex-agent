"""3-Tier Smart Auto-Fallback Engine."""
from __future__ import annotations

from typing import List, Optional
from apex.config import config


class FallbackRouter:
    """Provides fallback model recommendations when primary providers hit rate limits or downtime."""

    def __init__(self) -> None:
        pass

    def get_fallback_chain(self, failed_model: str) -> List[str]:
        """Generate an ordered list of fallback models to attempt next."""
        tiers = config.get("fallback_tiers", {})
        tier_1 = tiers.get("tier_1_subscription", ["claude-3-7-sonnet-latest", "gpt-4o"])
        tier_2 = tiers.get("tier_2_cheap", ["deepseek-chat", "gpt-4o-mini", "llama-3.3-70b-versatile"])
        tier_3 = tiers.get("tier_3_free", ["deepseek/deepseek-r1:free", "qwen2.5-coder:7b"])

        chain: list[str] = []

        # Find which tier the failed model belongs to
        if failed_model in tier_1:
            # Fallback to remaining in tier 1, then all of tier 2, then tier 3
            chain = [m for m in tier_1 if m != failed_model] + tier_2 + tier_3
        elif failed_model in tier_2:
            # Fallback to remaining in tier 2, then tier 3
            chain = [m for m in tier_2 if m != failed_model] + tier_3
        else:
            # Already in tier 3 or custom; try tier 2 then other tier 3
            chain = tier_2 + [m for m in tier_3 if m != failed_model]

        return chain

    def is_retryable_error(self, status_code: int, error_text: str = "") -> bool:
        """Check if an HTTP error code or message qualifies for auto-fallback."""
        # 429: Rate Limit, 402: Payment Required / Insufficient Quota,
        # 500, 502, 503, 504, 529: Server Down / Overloaded
        if status_code in [429, 402, 500, 502, 503, 504, 529]:
            return True
        err_lower = error_text.lower()
        if any(term in err_lower for term in ["rate limit", "quota", "overloaded", "capacity", "credits"]):
            return True
        return False


# Global fallback router instance
fallback_router = FallbackRouter()
