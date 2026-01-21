# dsat/services/llm.py

"""
Unified, asynchronous LLM service powered by LiteLLM.
Provides a simple interface for standard calls, structured JSON output,
and automatic cost tracking.
"""
import logging
import asyncio
import yaml
import copy
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Type, Optional, Any, Dict, List

import litellm
from pydantic import BaseModel, ValidationError

from dsat.config import LLMConfig # Use the main pydantic config
from dsat.common.exceptions import LLMError

logger = logging.getLogger(__name__)

# Configure LiteLLM globally
litellm.telemetry = False # Disable anonymous telemetry
litellm.input_callbacks = []
litellm.success_callbacks = []
litellm.failure_callbacks = []

# Load custom model pricing from YAML configuration file
def _load_custom_model_pricing():
    """Load custom model pricing configuration from config.yaml file."""
    try:
        # Get the path to the config.yaml file relative to this module
        current_dir = Path(__file__).parent
        framework_dir = current_dir.parent.parent  # Go up to ds_agent_framework
        config_yaml_path = framework_dir / "config.yaml"
        
        if config_yaml_path.exists():
            with open(config_yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('custom_model_pricing', {})
        else:
            # Changed to debug to avoid confusing warnings for pip-installed packages
            logger.debug(f"Config file not found at {config_yaml_path} (this is expected for pip-installed packages)")
            return {}
    except Exception as e:
        logger.error(f"Failed to load cost configuration: {e}")
        return {}

# Load and apply custom model pricing
CUSTOM_MODEL_PRICING = _load_custom_model_pricing()
if CUSTOM_MODEL_PRICING:
    litellm.model_cost.update(CUSTOM_MODEL_PRICING)
    logger.info(f"Loaded custom model pricing for {len(CUSTOM_MODEL_PRICING)} models")

class LLMService:
    """
    A robust wrapper around LiteLLM that handles requests, structured formatting,
    and cost tracking. It's configured via the main DSATConfig's LLMConfig.
    """
    def __init__(self, config: LLMConfig):
        self.config = config
        self.total_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_prompt_cost = 0.0
        self.total_completion_cost = 0.0
        self.call_history: List[Dict[str, Any]] = []

        # Get API keys using the new get_api_keys() method
        self.api_keys = config.get_api_keys()
        self.current_key_index = 0

        if not self.api_keys or all(not k for k in self.api_keys):
            raise ValueError(
                f"No API keys configured for model '{config.model}'. "
                f"Please set API_KEY environment variable or configure api_keys in LLM_MODEL_CONFIGS."
            )

        logger.info(f"Initialized LLM service for '{config.model}' with {len(self.api_keys)} API keys")

    def _get_current_api_key(self) -> str:
        """Get current API key from the pool."""
        return self.api_keys[self.current_key_index]

    def _switch_api_key(self) -> bool:
        """Switch to next API key in pool. Returns True if switched, False if no more keys."""
        if len(self.api_keys) <= 1:
            return False
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"Switching to API key {self.current_key_index + 1}/{len(self.api_keys)}")
        return True

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determines whether an error is retryable based on litellm exception types.
        Only network timeouts, rate limits, and temporary service issues should be retried.
        Authentication errors, invalid requests, and other permanent failures should not be retried.
        """
        # Import litellm exceptions locally to avoid import issues
        try:
            import litellm.exceptions as litellm_exceptions
        except ImportError:
            # If litellm exceptions module is not available, be conservative and retry
            return True
            
        # Non-retryable errors - fail immediately
        non_retryable_errors = (
            litellm_exceptions.AuthenticationError,  # API key issues
            litellm_exceptions.InvalidRequestError,  # Request format/parameter issues  
            litellm_exceptions.PermissionDeniedError,  # Insufficient permissions
            litellm_exceptions.NotFoundError,  # Model/endpoint not found
        )
        
        # Retryable errors - can be retried
        retryable_errors = (
            litellm_exceptions.RateLimitError,  # Rate limit exceeded
            litellm_exceptions.ServiceUnavailableError,  # Temporary service issues
            litellm_exceptions.Timeout,  # Network timeout
            litellm_exceptions.APIConnectionError,  # Connection issues
            litellm_exceptions.InternalServerError,  # Server-side temporary issues
        )
        
        # Check for specific error types
        if isinstance(error, non_retryable_errors):
            return False
        elif isinstance(error, retryable_errors):
            return True
        else:
            # For unknown errors, be conservative and retry
            # This handles generic network errors, etc.
            return True

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

    async def _make_llm_call_with_retries(
        self, messages: list, response_format: Optional[dict] = None, max_retries: int = 3, base_delay: float = 1.0
    ):
        """
        Internal method to make LLM calls with centralized retry logic and exponential backoff.
        This method is the single point of contact with the LiteLLM library.

        Args:
            messages: List of message dictionaries for the LLM.
            response_format: Optional response format specification.
            max_retries: Maximum number of retry attempts.
            base_delay: Base delay in seconds for exponential backoff.

        Returns:
            The raw LiteLLM response object upon success.

        Raises:
            LLMError: If all retry attempts fail due to API errors or empty responses.
        """
        if response_format and not self._supports_response_format():
            logger.info(
                "Dropping unsupported `response_format` for model %s; using prompt-enforced JSON instead.",
                self.config.model,
            )
            response_format = None

        logger.info(f"prompt: {messages[-1]['content']}")
        last_exception = None
        for attempt in range(max_retries):
            call_id = uuid.uuid4().hex
            call_started_at = datetime.utcnow()
            perf_start = time.perf_counter()
            try:
                kwargs = {
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "api_key": self._get_current_api_key(),
                    "api_base": self.config.api_base
                }
                if self.config.provider:
                    kwargs["custom_llm_provider"] = self.config.provider

                if response_format:
                    kwargs["response_format"] = response_format

                response = await litellm.acompletion(**kwargs)

                try:
                    content = response.choices[0].message.content
                    if content and content.strip():
                        duration = time.perf_counter() - perf_start
                        self._record_successful_call(
                            call_id=call_id,
                            call_started_at=call_started_at,
                            duration=duration,
                            messages=messages,
                            response=response,
                            content=content,
                            response_format=response_format
                        )
                        return response  # Success!
                    else:
                        # Treat empty response as a failure to be retried
                        logger.warning(f"LLM returned an empty response on attempt {attempt + 1}/{max_retries}.")
                        last_exception = LLMError("LLM returned an empty response.")
                except (IndexError, AttributeError) as content_error:
                    logger.warning(f"Invalid response structure on attempt {attempt + 1}/{max_retries}: {content_error}")
                    last_exception = LLMError(f"Invalid response structure: {content_error}")

            except Exception as e:
                # Special handling for RateLimitError - switch API key immediately
                import litellm.exceptions as litellm_exceptions
                if isinstance(e, litellm_exceptions.RateLimitError):
                    logger.warning(f"RateLimitError on attempt {attempt + 1}/{max_retries}: {e}")
                    if self._switch_api_key():
                        logger.info(f"Switched to next API key, retrying immediately...")
                        last_exception = e
                        continue  # Skip delay, retry immediately with new key
                    else:
                        logger.warning(f"No more API keys to switch, will use retry delay")
                        last_exception = e
                elif isinstance(e, litellm_exceptions.APIError) and self._is_insufficient_balance_error(e):
                    logger.warning(f"Insufficient balance on attempt {attempt + 1}/{max_retries}: {e}")
                    if self._switch_api_key():
                        logger.info("Switched to next API key after insufficient balance, retrying immediately...")
                        last_exception = e
                        continue
                    else:
                        logger.warning("No more API keys to switch after insufficient balance, will use retry delay")
                        last_exception = e
                # Check if this is a retryable error
                elif self._is_retryable_error(e):
                    logger.warning(f"Retryable LLM error on attempt {attempt + 1}/{max_retries}: {e}")
                    last_exception = e
                    logger.debug(f"Debug info - messages: {messages}, response_format: {response_format if response_format else 'None'}")
                else:
                    # Non-retryable error - fail immediately
                    logger.error(f"Non-retryable LLM error: {e}")
                    raise LLMError(f"LLM call failed with non-retryable error: {e}") from e

            # If this was the last attempt, break the loop to raise the final error
            if attempt == max_retries - 1:
                break

            # Exponential backoff with jitter
            delay = base_delay * (3 ** attempt) + (asyncio.get_event_loop().time() % 1)
            logger.info(f"Retrying LLM call in {delay:.2f} seconds ({attempt + 2}/{max_retries})...")
            await asyncio.sleep(delay)

        raise LLMError(f"LLM call failed after {max_retries} attempts. Last error: {last_exception}") from last_exception

    def _record_successful_call(
        self,
        call_id: str,
        call_started_at: datetime,
        duration: float,
        messages: list,
        response: Any,
        content: str,
        response_format: Optional[dict],
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

        self.total_cost += call_cost

        prompt_tokens = usage_payload.get("prompt_tokens") if usage_payload else None
        completion_tokens = usage_payload.get("completion_tokens") if usage_payload else None

        if prompt_tokens:
            self.total_prompt_tokens += prompt_tokens
        if completion_tokens:
            self.total_completion_tokens += completion_tokens

        prompt_cost_val = usage_payload.get("prompt_tokens_cost") if usage_payload else None
        completion_cost_val = usage_payload.get("completion_tokens_cost") if usage_payload else None

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
        logger.info(f"LLM call complete. Model: {self.config.model}, Cost: ${call_cost:.6f}")

    def _extract_usage(self, response: Any) -> Dict[str, Any]:
        """
        从 LiteLLM Response 中提取 token / 费用信息，确保可 JSON 序列化。
        """
        usage = getattr(response, "usage", None)
        if not usage:
            return {}

        payload: Dict[str, Any] = {
            "prompt_tokens": self._safe_int(getattr(usage, "prompt_tokens", None)),
            "completion_tokens": self._safe_int(getattr(usage, "completion_tokens", None)),
            "total_tokens": self._safe_int(getattr(usage, "total_tokens", None)),
            "prompt_tokens_cost": self._safe_float(getattr(usage, "prompt_tokens_cost", None)),
            "completion_tokens_cost": self._safe_float(getattr(usage, "completion_tokens_cost", None)),
        }
        total_tokens_cost = self._safe_float(getattr(usage, "total_tokens_cost", None))
        if total_tokens_cost is None:
            prompt_cost = payload.get("prompt_tokens_cost")
            completion_cost = payload.get("completion_tokens_cost")
            if prompt_cost is not None and completion_cost is not None:
                total_tokens_cost = prompt_cost + completion_cost
        payload["total_tokens_cost"] = total_tokens_cost
        return payload

    async def call(self, prompt: str, system_message: Optional[str] = None, max_retries: Optional[int] = None) -> str:
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

        logger.debug(f"Calling LLM ({self.config.model}) with prompt: {prompt[:100]}...")

        response = await self._make_llm_call_with_retries(messages, max_retries=retries)
        content = response.choices[0].message.content
        logger.info(f"content: {content}")
        return content

    async def call_with_json(self, prompt: str, output_model: Type[BaseModel], max_retries: Optional[int] = None) -> BaseModel:
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
            {"role": "user", "content": prompt_with_schema}
        ]

        logger.debug(f"Calling LLM ({self.config.model}) for structured JSON output...")

        for attempt in range(max(1, retries)):
            if self._supports_response_format():
                response = await self._make_llm_call_with_retries(
                    messages,
                    response_format={"type": "json_object"},
                    max_retries=retries,
                )
            else:
                if attempt == 0:
                    logger.info(
                        "Model %s does not support `response_format`; falling back to prompt-enforced JSON.",
                        self.config.model,
                    )
                response = await self._make_llm_call_with_retries(
                    messages,
                    response_format=None,
                    max_retries=retries,
                )

            try:
                response_content = response.choices[0].message.content
                logger.info(f"content: {response_content}")
            except (IndexError, AttributeError) as e:
                raise LLMError(f"Invalid response structure from LLM: {e}") from e

            try:
                return output_model.model_validate_json(response_content)
            except ValidationError as e:
                logger.error(
                    "Failed to validate LLM JSON response against Pydantic model (attempt %d/%d): %s",
                    attempt + 1,
                    retries,
                    e,
                )
                logger.debug("Invalid JSON received: %s", response_content)
                if attempt + 1 >= retries:
                    raise LLMError(
                        f"LLM returned invalid JSON that could not be parsed: {e}"
                    ) from e

    def get_total_cost(self) -> float:
        """Returns the total accumulated cost for this LLM instance."""
        return self.total_cost

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Returns a deep copy of the call history for telemetry persistence."""
        return copy.deepcopy(self.call_history)

    def get_usage_summary(self) -> Dict[str, Any]:
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
