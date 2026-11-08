"""Apex Router: 9Router / 9Router Pro Engine."""
from __future__ import annotations

from apex.router.rtk import rtk_compressor, RTKTokenSaver
from apex.router.key_pool import key_pool, KeyPool
from apex.router.fallback import fallback_router, FallbackRouter
from apex.router.injector import prompt_injector, PromptInjector
from apex.router.ledger import token_ledger, TokenLedger
from apex.router.provider_manager import provider_manager, ProviderManager
from apex.router.model_switcher import model_switcher, ModelSwitcher

__all__ = [
    "rtk_compressor",
    "RTKTokenSaver",
    "key_pool",
    "KeyPool",
    "fallback_router",
    "FallbackRouter",
    "prompt_injector",
    "PromptInjector",
    "token_ledger",
    "TokenLedger",
    "provider_manager",
    "ProviderManager",
    "model_switcher",
    "ModelSwitcher",
]
