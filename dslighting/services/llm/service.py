# service.py

"""
LLM service implementation powered by LiteLLM.

Provides:
- LLMService: Main service for making LLM calls with cost tracking
- CachedLLMService: Cached wrapper for LLM responses
"""

from __future__ import annotations

import asyncio
import copy
from contextlib import asynccontextmanager
import hashlib
import logging
import os
import threading
import time
import weakref
from datetime import datetime
from typing import TYPE_CHECKING, Any

import litellm
from pydantic import BaseModel

from dslighting.config import LLMConfig
from dslighting.debug.api import get_debug_session
from dslighting.error import LLMServiceError
from dslighting.services.llm.cost import apply_custom_model_pricing
from dslighting.services.llm.executor import LLMCallExecutor, LLMCallSpec
from dslighting.services.llm.observed_call import extract_usage, serialize_response_for_debug
from dslighting.services.llm.pool import GlobalAPIKeyPool
from dslighting.utils.constants import (
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_MAX_CONCURRENT_PER_KEY,
)

# Ensure custom pricing is applied
apply_custom_model_pricing()

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

# Configure LiteLLM globally
litellm.telemetry = False  # Disable anonymous telemetry
litellm.input_callbacks = []
litellm.success_callbacks = []
litellm.failure_callbacks = []


class LLMService:
    """
    A robust wrapper around LiteLLM that handles requests, structured formatting,
    and cost tracking. It's configured via the main DSLightingConfig's LLMConfig.
    """

    _concurrency_mutex = threading.RLock()
    _global_limit: int | None = None
    _global_semaphores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]" = weakref.WeakKeyDictionary()
    _model_limits: dict[str, int] = {}
    _model_semaphores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, dict[str, asyncio.Semaphore]]" = weakref.WeakKeyDictionary()

    # Global cost tracking across all LLMService instances
    _global_total_cost: float = 0.0
    _global_cost_mutex = threading.RLock()

    @classmethod
    def normalize_concurrency_limits(
        cls,
        *,
        global_max_concurrency: int | None = None,
        model_quotas: dict[str, Any] | None = None,
    ) -> tuple[int | None, dict[str, int]]:
        """Normalize concurrency limits into a stable, comparable representation."""
        normalized_global = cls._normalize_positive_int(global_max_concurrency)
        normalized_model_limits: dict[str, int] = {}
        for raw_model, raw_cap in (model_quotas or {}).items():
            model_name = cls._normalize_model_name(raw_model)
            cap = cls._normalize_positive_int(raw_cap)
            if not model_name or cap is None:
                continue
            normalized_model_limits[model_name] = cap
        return normalized_global, normalized_model_limits

    @classmethod
    def _concurrency_limit_signature(
        cls,
        *,
        global_max_concurrency: int | None = None,
        model_quotas: dict[str, Any] | None = None,
    ) -> tuple[int | None, tuple[tuple[str, int], ...]]:
        normalized_global, normalized_model_limits = cls.normalize_concurrency_limits(
            global_max_concurrency=global_max_concurrency,
            model_quotas=model_quotas,
        )
        return normalized_global, tuple(sorted(normalized_model_limits.items()))

    @classmethod
    def configure_concurrency_limits(
        cls,
        *,
        global_max_concurrency: int | None = None,
        model_quotas: dict[str, Any] | None = None,
    ) -> None:
        """
        Configure process-wide LLM concurrency limits.

        Args:
            global_max_concurrency: Global in-flight request cap.
            model_quotas: Per-model in-flight request caps.
        """
        with cls._concurrency_mutex:
            normalized_global, normalized_model_limits = cls.normalize_concurrency_limits(
                global_max_concurrency=global_max_concurrency,
                model_quotas=model_quotas,
            )
            previous_signature = (
                cls._global_limit,
                tuple(sorted(cls._model_limits.items())),
            )
            next_signature = (
                normalized_global,
                tuple(sorted(normalized_model_limits.items())),
            )
            if next_signature == previous_signature:
                return

            cls._global_limit = normalized_global
            cls._model_limits = normalized_model_limits

            # asyncio.Semaphore is loop-bound; reset caches so each event loop
            # lazily gets its own semaphore objects.
            cls._global_semaphores = weakref.WeakKeyDictionary()
            cls._model_semaphores = weakref.WeakKeyDictionary()

    @classmethod
    def _get_loop_concurrency_controls(
        cls,
    ) -> tuple[asyncio.Semaphore | None, dict[str, asyncio.Semaphore]]:
        """Get semaphores bound to the current running event loop."""
        loop = asyncio.get_running_loop()
        with cls._concurrency_mutex:
            global_sem = cls._global_semaphores.get(loop)
            if global_sem is None and cls._global_limit is not None:
                global_sem = asyncio.Semaphore(cls._global_limit)
                cls._global_semaphores[loop] = global_sem

            model_sems = cls._model_semaphores.get(loop)
            if model_sems is None:
                model_sems = {
                    model: asyncio.Semaphore(cap)
                    for model, cap in cls._model_limits.items()
                }
                cls._model_semaphores[loop] = model_sems
        return global_sem, model_sems

    @staticmethod
    def _normalize_model_name(model: Any) -> str:
        if not isinstance(model, str):
            return ""
        return model.strip()

    @staticmethod
    def _normalize_positive_int(value: Any) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def __init__(
        self,
        config: LLMConfig,
        max_concurrent_per_key: int | None = None,
    ):
        """
        初始化 LLM Service。

        Args:
            config: LLM 配置
            max_concurrent_per_key: 每个 API key 的最大并发数（默认读取配置，未配置时使用系统默认）
        """
        self.config = config

        configured_per_key = self._normalize_positive_int(max_concurrent_per_key)
        if configured_per_key is None:
            configured_per_key = self._normalize_positive_int(getattr(config, "max_concurrent_per_key", None))
        if configured_per_key is None:
            configured_per_key = self._normalize_positive_int(os.getenv("LLM_MAX_CONCURRENT_PER_KEY"))
        if configured_per_key is None:
            configured_per_key = DEFAULT_MAX_CONCURRENT_PER_KEY

        self.max_concurrent_per_key = configured_per_key
        self.total_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_prompt_cost = 0.0
        self.total_completion_cost = 0.0
        self.call_history: list[dict[str, Any]] = []
        self._executor = LLMCallExecutor(self)

        # Get API keys using the new get_api_keys() method
        api_keys = config.get_api_keys()

        if not api_keys or all(not k for k in api_keys):
            raise LLMServiceError(
                f"No API keys configured for model '{config.model}'. "
                f"Please set API_KEY environment variable or configure api_keys in LLM_MODEL_CONFIGS.",
                error_code="LLM-001",
                details={"model": config.model},
                suggestion="Set the API_KEY environment variable or configure api_keys in LLM_MODEL_CONFIGS",
            )

        # 使用全局共享的 API key 池（而不是 per-instance 的轮换）
        self._key_pool = GlobalAPIKeyPool.get_or_create_pool(
            model_name=config.model,
            keys=api_keys,
            max_concurrent_per_key=self.max_concurrent_per_key,
        )

        logger.info(
            f"Initialized LLM service for '{config.model}' with global shared key pool ({len(api_keys)} keys, {self.max_concurrent_per_key} concurrent per key)"
        )

        # Update monitoring with API key count
        try:
            from dslighting.monitoring.monitoring import get_global_monitor

            monitor = get_global_monitor()
            if monitor is not None:
                monitor.set_active_keys(len(api_keys), len(api_keys))
        except Exception:
            pass  # Silently fail if monitoring is unavailable

    @staticmethod
    def _structured_debug_enabled() -> bool:
        session = get_debug_session()
        return bool(session and session.enabled and session.config.console_output)

    @asynccontextmanager
    async def _concurrency_guard(self) -> AsyncGenerator[None, None]:
        """
        Acquire global and model-level semaphores before issuing a provider call.
        """
        global_sem, model_sems = self._get_loop_concurrency_controls()
        model_sem = model_sems.get(self._normalize_model_name(self.config.model))

        acquired_global = False
        acquired_model = False
        try:
            if global_sem is not None:
                await global_sem.acquire()
                acquired_global = True
            if model_sem is not None:
                await model_sem.acquire()
                acquired_model = True
            yield
        finally:
            if model_sem is not None and acquired_model:
                model_sem.release()
            if global_sem is not None and acquired_global:
                global_sem.release()

    def _get_current_api_key(self) -> str:
        """Get current API key from the pool."""
        # API keys are managed by GlobalAPIKeyPool
        # This method is kept for potential backward compatibility
        return self._key_pool.keys[0]

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _serialize_response_for_debug(response: Any) -> dict[str, Any]:
        """Convert provider response objects into JSON-serializable dict for debug logging."""
        return serialize_response_for_debug(response)

    def _build_completion_kwargs(
        self,
        *,
        messages: list,
        response_format: dict | None,
        api_key: str,
    ) -> dict[str, Any]:
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "api_key": api_key,
            "api_base": self.config.api_base,
        }
        if self.config.provider:
            kwargs["custom_llm_provider"] = self.config.provider
        if response_format:
            kwargs["response_format"] = response_format
        return kwargs

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determines whether an error is retryable based on litellm exception types.
        Only network timeouts, rate limits, and temporary service issues should be retried.
        Authentication errors, invalid requests, and other permanent failures should not be retried.
        """
        return self._classify_error_action(error) != "fail_fast"

    def _classify_error_action(self, error: Exception) -> str:
        """
        Classify provider failures into runtime actions.

        Returns one of:
        - retry_same_key: transient/network/provider issue on the current key
        - retry_next_key: key-specific auth/quota issue, rotate to another key
        - fail_fast: malformed request or permanent call failure
        """
        # Import litellm exceptions locally to avoid import issues
        try:
            import litellm.exceptions as litellm_exceptions
        except ImportError:
            # If litellm exceptions module is not available, be conservative and retry
            return "retry_same_key"

        if self._is_insufficient_balance_error(error):
            return "retry_next_key"

        key_specific_errors = (
            litellm_exceptions.AuthenticationError,  # API key issues
            litellm_exceptions.PermissionDeniedError,  # Key/account level permission issues
        )
        if isinstance(error, key_specific_errors):
            return "retry_next_key"

        fail_fast_errors = (
            litellm_exceptions.InvalidRequestError,  # Request format/parameter issues
            litellm_exceptions.NotFoundError,  # Model/endpoint not found
        )
        if isinstance(error, fail_fast_errors):
            return "fail_fast"

        retryable_errors = (
            litellm_exceptions.RateLimitError,  # Rate limit exceeded
            litellm_exceptions.ServiceUnavailableError,  # Temporary service issues
            litellm_exceptions.Timeout,  # Network timeout
            litellm_exceptions.APIConnectionError,  # Connection issues
            litellm_exceptions.InternalServerError,  # Server-side temporary issues
        )
        if isinstance(error, retryable_errors):
            return "retry_same_key"

        message = str(error).lower()
        if "api key is invalid" in message or "invalid api key" in message or "authentication" in message:
            return "retry_next_key"
        return "retry_same_key"

    def _supports_response_format(self) -> bool:
        """
        Whether it's safe to pass `response_format` through LiteLLM for this model.

        Some OpenAI reasoning models (e.g. `o4-mini-*`) reject `response_format` and
        require JSON-only behavior to be enforced via prompt instead.
        """
        raw_model = (self.config.model or "").strip()
        model = raw_model.split("/")[-1].strip()
        model_lower = model.lower()
        if model_lower.startswith("o4-mini-") or model_lower == "o4-mini":
            return False
        if model_lower == "kimi-k2-instruct-0905":
            return False
        return True

    @staticmethod
    def _is_insufficient_balance_error(error: Exception) -> bool:
        """
        Detect insufficient balance/quota errors that should trigger API key rotation.
        """
        message = str(error).lower()
        return (
            "insufficient" in message and "balance" in message
        ) or "insufficient_quota" in message or "insufficient quota" in message

    def _cooldown_seconds_for_error(self, error: Exception) -> float:
        """Return a conservative cooldown window for a failed key."""
        if self._is_insufficient_balance_error(error):
            return 600.0
        action = self._classify_error_action(error)
        if action == "retry_next_key":
            return 1800.0
        if action == "retry_same_key":
            return 60.0
        return 0.0

    async def _make_llm_call_with_retries(
        self,
        messages: list,
        response_format: dict | None = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        """
        Backward-compatible wrapper retained for advanced callers that still use the
        old private helper. Internally it now routes through the unified executor.
        """
        return await self.call_messages(
            messages=messages,
            max_retries=max_retries,
            response_format=response_format,
        )

    def _record_successful_call(
        self,
        call_id: str,
        call_started_at: datetime,
        duration: float,
        messages: list,
        response: Any,
        content: str,
        response_format: dict | None,
    ) -> None:
        """
        将一次成功的调用附加到历史中，并更新累计 token / 费用。
        """
        usage_payload = self._extract_usage(response)
        try:
            call_cost_raw = litellm.completion_cost(completion_response=response)
            call_cost = float(call_cost_raw) if call_cost_raw is not None else 0.0
        except Exception:
            call_cost = 0.0

        # Extract tokens for monitoring
        prompt_tokens = usage_payload.get("prompt_tokens", 0) if usage_payload else 0
        completion_tokens = (
            usage_payload.get("completion_tokens", 0) if usage_payload else 0
        )

        # Update global monitoring if available
        try:
            from dslighting.monitoring.monitoring import get_global_monitor

            monitor = get_global_monitor()
            if monitor is not None:
                # Convert duration to milliseconds for P95/P99 latency tracking
                latency_ms = duration * 1000.0
                monitor.record_llm_request(
                    latency_ms=latency_ms,
                    cost=call_cost,
                    input_tokens=prompt_tokens,
                    output_tokens=completion_tokens,
                )
        except Exception:
            pass  # Silently fail if monitoring is unavailable

        self.total_cost += call_cost

        # Update global total cost across all instances
        with LLMService._global_cost_mutex:
            LLMService._global_total_cost += call_cost

        prompt_tokens = usage_payload.get("prompt_tokens") if usage_payload else None
        completion_tokens = (
            usage_payload.get("completion_tokens") if usage_payload else None
        )

        if prompt_tokens:
            self.total_prompt_tokens += prompt_tokens
        if completion_tokens:
            self.total_completion_tokens += completion_tokens

        prompt_cost_val = usage_payload.get("prompt_tokens_cost") if usage_payload else None
        completion_cost_val = (
            usage_payload.get("completion_tokens_cost") if usage_payload else None
        )

        if prompt_cost_val is not None:
            self.total_prompt_cost += prompt_cost_val
        if completion_cost_val is not None:
            self.total_completion_cost += completion_cost_val

        total_tokens = usage_payload.get("total_tokens") if usage_payload else None
        cost_per_token = (call_cost / total_tokens) if total_tokens else None

        history_entry = {
            "call_id": call_id,
            "model": self.config.model,
            "provider": self.config.provider,
            "timestamp_utc": call_started_at.isoformat() + "Z",
            "duration_seconds": round(duration, 4),
            "response_format": "json_object" if response_format else "text",
            "messages": copy.deepcopy(messages),
            "response": content,
            "usage": usage_payload or None,
            "cost": call_cost,
            "cost_per_token": cost_per_token,
        }
        self.call_history.append(history_entry)
        if not self._structured_debug_enabled():
            logger.debug(
                f"LLM call complete. Model: {self.config.model}, Cost: ${call_cost:.6f}"
            )

    def _extract_usage(self, response: Any) -> dict[str, Any]:
        """
        从 LiteLLM Response 中提取 token / 费用信息，确保可 JSON 序列化。
        """
        return extract_usage(response)

    async def call(
        self,
        prompt: str,
        system_message: str | None = None,
        max_retries: int | None = None,
    ) -> str:
        """
        Makes a standard, asynchronous call to the LLM and returns the text response.
        The retry logic is handled by the internal _make_llm_call_with_retries method.

        Args:
            prompt: The user's prompt.
            system_message: An optional system message to guide the LLM's behavior.
            max_retries: Maximum number of retry attempts (default: 3).

        Returns:
            The string content of the LLM's response.
        """
        retries = max_retries if max_retries is not None else self.config.max_retries
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        if not self._structured_debug_enabled():
            logger.debug(
                f"Calling LLM ({self.config.model}) with prompt: {prompt[:100]}..."
            )

        response = await self._executor.execute(
            LLMCallSpec(
                messages=messages,
                response_mode="text",
                max_transport_retries=retries,
                max_validation_retries=1,
            )
        )
        content = response.choices[0].message.content
        return content

    async def call_messages(
        self,
        messages: list[dict[str, Any]],
        max_retries: int | None = None,
        response_format: dict | None = None,
    ) -> Any:
        """
        Makes an asynchronous multi-turn call to the LLM and returns the raw response.

        Args:
            messages: Full message list to send.
            max_retries: Maximum transport retry attempts.
            response_format: Optional response format specification.

        Returns:
            The raw LiteLLM response object.
        """
        retries = max_retries if max_retries is not None else self.config.max_retries
        return await self._executor.execute(
            LLMCallSpec(
                messages=messages,
                response_format=response_format,
                response_mode="text",
                max_transport_retries=retries,
                max_validation_retries=1,
            )
        )

    async def call_with_json(
        self,
        prompt: str,
        output_model: type[BaseModel],
        max_retries: int | None = None,
    ) -> BaseModel:
        """
        Calls the LLM and forces the output to be a JSON object conforming to the
        provided Pydantic model. The retry logic is handled by the internal method.

        Args:
            prompt: The user's prompt.
            output_model: The Pydantic model class for the desired output structure.
            max_retries: Maximum number of retry attempts (default: 3).

        Returns:
            An instantiated Pydantic model with the LLM's response.
        """
        retries = max_retries if max_retries is not None else self.config.max_retries
        system_message = (
            "You are a helpful assistant that always responds with a JSON object "
            "that strictly adheres to the provided JSON Schema. Do not add any "
            "other text, explanations, or markdown formatting."
        )

        prompt_with_schema = (
            f"{prompt}\n\n# RESPONSE JSON SCHEMA:\n"
            f"```json\n{output_model.model_json_schema()}\n```"
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt_with_schema},
        ]

        if not self._structured_debug_enabled():
            logger.debug(
                f"Calling LLM ({self.config.model}) for structured JSON output..."
            )

        response_format = {"type": "json_object"} if self._supports_response_format() else None
        if response_format is None and not self._structured_debug_enabled():
            logger.debug(
                "Model %s does not support `response_format`; falling back to prompt-enforced JSON.",
                self.config.model,
            )

        return await self._executor.execute(
            LLMCallSpec(
                messages=messages,
                response_format=response_format,
                output_model=output_model,
                response_mode="json",
                max_transport_retries=retries,
                max_validation_retries=max(1, retries),
            )
        )

    def get_total_cost(self) -> float:
        """Returns the total accumulated cost for this LLM instance."""
        return self.total_cost

    @classmethod
    def get_global_total_cost(cls) -> float:
        """
        Returns the total accumulated cost across all LLMService instances.

        This is useful for monitoring total LLM API costs in a benchmark scenario
        where multiple LLMService instances may be created.

        Returns:
            The total cost accumulated across all instances
        """
        with cls._global_cost_mutex:
            return cls._global_total_cost

    def get_call_history(self) -> list[dict[str, Any]]:
        """Returns a deep copy of the call history for telemetry persistence."""
        return copy.deepcopy(self.call_history)

    def get_usage_summary(self) -> dict[str, Any]:
        """汇总本实例的 token/费用信息。"""
        total_tokens = self.total_prompt_tokens + self.total_completion_tokens
        summary = {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": total_tokens,
            "prompt_tokens_cost": round(self.total_prompt_cost, 12),
            "completion_tokens_cost": round(self.total_completion_cost, 12),
            "total_cost": round(self.total_cost, 12),
            "call_count": len(self.call_history),
        }
        summary["cost_per_token"] = (self.total_cost / total_tokens) if total_tokens else None
        return summary

    def with_cache(self, cache_ttl: int = DEFAULT_CACHE_TTL_SECONDS) -> "CachedLLMService":
        """
        Create a CachedLLMService wrapper for this LLMService instance.

        This provides optional caching capabilities without modifying the original service.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)

        Returns:
            A CachedLLMService instance wrapping this service

        Example:
            llm = LLMService(config)
            cached_llm = llm.with_cache(cache_ttl=7200)
            response = await cached_llm.call_with_cache("Hello!")
        """
        return CachedLLMService(self.config, cache_ttl=cache_ttl)

    async def batch_call(
        self,
        prompts: list[str],
        system_message: str | None = None,
        max_retries: int | None = None,
        batch_size: int = 20,
    ) -> list[str]:
        """
        Make multiple LLM calls in batches for improved throughput.

        This method groups prompts into batches and processes them concurrently,
        significantly reducing total time for multiple calls. Batches are
        processed in sequence to avoid overwhelming the API.

        Args:
            prompts: List of prompts to process
            system_message: Optional system message for all prompts
            max_retries: Maximum number of retry attempts per prompt
            batch_size: Number of prompts to process concurrently (default: 20)

        Returns:
            List of responses in the same order as input prompts

        Example:
            llm = LLMService(config)
            prompts = ["Analyze data A", "Analyze data B", "Analyze data C"]
            responses = await llm.batch_call(prompts, batch_size=10)
        """
        if not prompts:
            return []

        logger.debug(
            f"Batch processing {len(prompts)} prompts with batch_size={batch_size}"
        )

        responses: list[str | None] = [None] * len(prompts)

        # Process in batches
        for batch_start in range(0, len(prompts), batch_size):
            batch_end = min(batch_start + batch_size, len(prompts))
            batch_prompts = prompts[batch_start:batch_end]

            logger.debug(
                f"Processing batch {batch_start // batch_size + 1}: prompts {batch_start}-{batch_end}"
            )

            # Create tasks for concurrent processing
            batch_indices: list[int] = []
            tasks = []
            for i, prompt in enumerate(batch_prompts):
                batch_indices.append(batch_start + i)
                task = self.call(prompt, system_message=system_message, max_retries=max_retries)
                tasks.append(task)

            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            for idx, result in zip(batch_indices, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in prompt {idx}: {result}")
                    responses[idx] = f"Error: {str(result)}"
                else:
                    responses[idx] = result

            logger.debug(f"Batch {batch_start // batch_size + 1} complete")

        logger.debug(f"Batch processing complete: {len(responses)} responses")
        return responses  # type: ignore[return-value]

    async def batch_call_with_json(
        self,
        prompts: list[str],
        output_model: type[BaseModel],
        max_retries: int | None = None,
        batch_size: int = 20,
    ) -> list[BaseModel | None]:
        """
        Make multiple LLM calls with JSON output in batches.

        Similar to batch_call but enforces JSON schema validation for each response.

        Args:
            prompts: List of prompts to process
            output_model: Pydantic model for response validation
            max_retries: Maximum number of retry attempts per prompt
            batch_size: Number of prompts to process concurrently

        Returns:
            List of validated Pydantic models

        Example:
            llm = LLMService(config)
            prompts = ["Extract entities from A", "Extract entities from B"]
            results = await llm.batch_call_with_json(prompts, EntityExtraction)
        """
        if not prompts:
            return []

        logger.debug(
            f"Batch JSON processing {len(prompts)} prompts with batch_size={batch_size}"
        )

        responses: list[BaseModel | None] = [None] * len(prompts)

        for batch_start in range(0, len(prompts), batch_size):
            batch_end = min(batch_start + batch_size, len(prompts))
            batch_prompts = prompts[batch_start:batch_end]

            logger.debug(
                f"Processing JSON batch {batch_start // batch_size + 1}: prompts {batch_start}-{batch_end}"
            )

            batch_indices: list[int] = []
            tasks = []
            for i, prompt in enumerate(batch_prompts):
                batch_indices.append(batch_start + i)
                task = self.call_with_json(prompt, output_model, max_retries=max_retries)
                tasks.append(task)

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in zip(batch_indices, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in prompt {idx}: {result}")
                    # Create a dummy instance or handle error as needed
                    responses[idx] = None
                else:
                    responses[idx] = result

            logger.debug(f"JSON batch {batch_start // batch_size + 1} complete")

        logger.debug(f"Batch JSON processing complete: {len(responses)} responses")
        return responses


class CachedLLMService:
    """
    LLMService wrapper that provides response caching for identical prompts.

    This class caches LLM responses based on prompt content and system message,
    reducing API calls and costs for repeated or similar requests.
    """

    def __init__(self, config: LLMConfig, cache_ttl: int = DEFAULT_CACHE_TTL_SECONDS):
        """
        Initialize the cached LLM service.

        Args:
            config: LLM configuration
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self._service = LLMService(config)
        self._cache_ttl = cache_ttl
        self._response_cache: dict[str, tuple[str, float]] = {}

    def _generate_cache_key(self, prompt: str, system_message: str | None = None) -> str:
        """
        Generate a unique cache key for the prompt and system message.

        Args:
            prompt: The user's prompt
            system_message: Optional system message

        Returns:
            A unique hash string for the cache key
        """
        content = prompt + (system_message or "")
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    async def call_with_cache(
        self, prompt: str, system_message: str | None = None
    ) -> str:
        """
        Call LLM with caching for identical prompts.

        If a cached response exists and hasn't expired, returns the cached response.
        Otherwise, makes the actual LLM call and caches the result.

        Args:
            prompt: The user's prompt
            system_message: Optional system message

        Returns:
            The LLM response (either cached or fresh)
        """
        cache_key = self._generate_cache_key(prompt, system_message)
        current_time = time.time()

        if cache_key in self._response_cache:
            cached_response, timestamp = self._response_cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for prompt (key: {cache_key[:8]}...)")
                return cached_response
            else:
                logger.debug(f"Cache expired for key {cache_key[:8]}...")
                del self._response_cache[cache_key]

        response = await self._service.call(prompt, system_message)
        self._response_cache[cache_key] = (response, current_time)
        logger.debug(f"Cached response for key {cache_key[:8]}...")
        return response

    async def call_with_json_with_cache(
        self,
        prompt: str,
        output_model: type[BaseModel],
        system_message: str | None = None,
    ) -> BaseModel:
        """
        Call LLM with JSON output and caching.

        Note: Caching for JSON responses uses the prompt as the key.
        The cached response will be parsed into the output model type.

        Args:
            prompt: The user's prompt
            output_model: Pydantic model class for response validation
            system_message: Optional system message

        Returns:
            Validated Pydantic model instance
        """
        cache_key = self._generate_cache_key(prompt, system_message)
        current_time = time.time()

        if cache_key in self._response_cache:
            cached_response, timestamp = self._response_cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for JSON prompt (key: {cache_key[:8]}...)")
                # Parse cached JSON string back into the model
                return output_model.model_validate_json(cached_response)
            else:
                logger.debug(f"Cache expired for key {cache_key[:8]}...")
                del self._response_cache[cache_key]

        response = await self._service.call_with_json(prompt, output_model)
        # Store as JSON string for cache
        cached_json = response.model_dump_json()
        self._response_cache[cache_key] = (cached_json, current_time)
        logger.debug(f"Cached JSON response for key {cache_key[:8]}...")
        return response

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self._response_cache.clear()
        logger.debug("LLM response cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0

        for key, (response, timestamp) in self._response_cache.items():
            if current_time - timestamp < self._cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": len(self._response_cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_ttl_seconds": self._cache_ttl,
        }

    @property
    def underlying_service(self) -> LLMService:
        """Access the underlying LLMService instance."""
        return self._service

    def get_total_cost(self) -> float:
        """Get total cost from the underlying service."""
        return self._service.get_total_cost()

    def get_call_history(self) -> list[dict[str, Any]]:
        """Get call history from the underlying service."""
        return self._service.get_call_history()

    def get_usage_summary(self) -> dict[str, Any]:
        """Get usage summary from the underlying service."""
        return self._service.get_usage_summary()
