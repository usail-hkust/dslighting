# __init__.py

"""
LLM services module.

This module provides unified, asynchronous LLM service powered by LiteLLM.
It includes classes for making LLM calls, managing API key pools,
and tracking costs.

Submodules:
- service: LLMService and CachedLLMService classes
- pool: GlobalAPIKeyPool and LLMConnectionPool classes
- cost: Cost tracking and model pricing utilities

For backward compatibility, all classes are also re-exported at the package level.
"""

from __future__ import annotations

from dslighting.services.llm.service import CachedLLMService, LLMService
from dslighting.services.llm.pool import GlobalAPIKeyPool, LLMConnectionPool

__all__ = [
    "LLMService",
    "CachedLLMService",
    "GlobalAPIKeyPool",
    "LLMConnectionPool",
]
