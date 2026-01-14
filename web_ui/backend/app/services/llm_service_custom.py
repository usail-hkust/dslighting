# web_ui/backend/app/services/llm_service_custom.py

"""
Custom LLM service for the Web UI backend.
Includes enhanced colored logging and support for system personas in JSON calls.
"""
import logging
import asyncio
import yaml
import copy
import time
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Type, Optional, Any, Dict, List

import litellm
from pydantic import BaseModel, ValidationError

from dsat.config import LLMConfig
from dsat.common.exceptions import LLMError

logger = logging.getLogger(__name__)

# Configure LiteLLM globally
litellm.telemetry = False
litellm.input_callbacks = []
litellm.success_callbacks = []
litellm.failure_callbacks = []

# ANSI Colors
BLUE = "\033[94m"
GREEN = "\033[92m"
RESET = "\033[0m"

def _log_colored(title: str, content: str, color: str):
    """Helper to print colored, formatted logs."""
    sep = "=" * 80
    print(f"\n{color}{sep}")
    print(f"[{title}]")
    print(f"{content}")
    print(f"{sep}{RESET}\n")

def _load_custom_model_pricing():
    try:
        current_dir = Path(__file__).parent
        # Adjusted path for backend directory structure
        config_yaml_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "config.yaml"
        
        if config_yaml_path.exists():
            with open(config_yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('custom_model_pricing', {})
        return {}
    except Exception as e:
        logger.error(f"Failed to load cost configuration: {e}")
        return {}

CUSTOM_MODEL_PRICING = _load_custom_model_pricing()
if CUSTOM_MODEL_PRICING:
    litellm.model_cost.update(CUSTOM_MODEL_PRICING)

class CustomLLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.total_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_prompt_cost = 0.0
        self.total_completion_cost = 0.0
        self.call_history: List[Dict[str, Any]] = []

        import json
        try:
            self.api_keys = json.loads(config.api_key) if config.api_key and config.api_key.startswith('[') else [config.api_key]
        except:
            self.api_keys = [config.api_key]
        self.current_key_index = 0

    def _get_current_api_key(self) -> str:
        return self.api_keys[self.current_key_index]

    def _switch_api_key(self) -> bool:
        if len(self.api_keys) <= 1:
            return False
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return True

    def _supports_response_format(self) -> bool:
        raw_model = (self.config.model or "").strip()
        model = raw_model.split("/")[-1].strip()
        model_lower = model.lower()
        if model_lower.startswith("o4-mini-") or model_lower == "o4-mini":
            return False
        if model_lower == "kimi-k2-instruct-0905":
            return False
        return True

    async def _make_llm_call_with_retries(
        self, messages: list, response_format: Optional[dict] = None, max_retries: int = 3, base_delay: float = 1.0
    ):
        if response_format and not self._supports_response_format():
            response_format = None

        # Enhanced Logging: Full History
        full_prompt_log = ""
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            full_prompt_log += f"[{role}]:\n{content}\n\n"
        _log_colored("LLM INPUT (PROMPT)", full_prompt_log.strip(), BLUE)

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
                content = response.choices[0].message.content
                if content and content.strip():
                    duration = time.perf_counter() - perf_start
                    self._record_successful_call(call_id, call_started_at, duration, messages, response, content, response_format)
                    return response
                last_exception = LLMError("LLM returned an empty response.")
            except Exception as e:
                import litellm.exceptions as litellm_exceptions
                if isinstance(e, (litellm_exceptions.RateLimitError, litellm_exceptions.APIError)):
                    if self._switch_api_key(): continue
                last_exception = e
                if attempt == max_retries - 1: break
                delay = base_delay * (3 ** attempt)
                await asyncio.sleep(delay)

        raise LLMError(f"LLM call failed after {max_retries} attempts. Last error: {last_exception}") from last_exception

    def _record_successful_call(self, call_id, call_started_at, duration, messages, response, content, response_format):
        usage = getattr(response, "usage", None)
        call_cost = 0.0
        try:
            call_cost_raw = litellm.completion_cost(completion_response=response)
            call_cost = float(call_cost_raw) if call_cost_raw is not None else 0.0
        except: pass
        self.total_cost += call_cost
        
        history_entry = {
            "call_id": call_id,
            "model": self.config.model,
            "timestamp_utc": call_started_at.isoformat() + "Z",
            "duration_seconds": round(duration, 4),
            "messages": copy.deepcopy(messages),
            "response": content,
            "cost": call_cost,
        }
        self.call_history.append(history_entry)
        logger.info(f"LLM call complete. Cost: ${call_cost:.6f}")

    async def call(self, prompt: str, system_message: Optional[str] = None, max_retries: Optional[int] = None) -> str:
        retries = max_retries if max_retries is not None else self.config.max_retries
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = await self._make_llm_call_with_retries(messages, max_retries=retries)
        content = response.choices[0].message.content
        _log_colored("LLM OUTPUT (RESPONSE)", content, GREEN)
        return content

    async def call_with_json(self, prompt: str, output_model: Type[BaseModel], max_retries: Optional[int] = None, system_message: Optional[str] = None) -> BaseModel:
        retries = max_retries if max_retries is not None else self.config.max_retries
        
        base_system = system_message or "You are a helpful assistant."
        json_instruction = "\n\nYou MUST respond with a JSON object that strictly adheres to the provided JSON Schema. Do not add any other text, explanations, or markdown formatting."
        final_system_message = base_system + json_instruction

        prompt_with_schema = f"{prompt}\n\n# RESPONSE JSON SCHEMA:\n```json\n{output_model.model_json_schema()}\n```"
        messages = [{"role": "system", "content": final_system_message}, {"role": "user", "content": prompt_with_schema}]

        for attempt in range(max(1, retries)):
            fmt = {"type": "json_object"} if self._supports_response_format() else None
            response = await self._make_llm_call_with_retries(messages, response_format=fmt, max_retries=retries)
            response_content = response.choices[0].message.content
            _log_colored("LLM OUTPUT (JSON RESPONSE)", response_content, GREEN)
            try:
                return output_model.model_validate_json(response_content)
            except ValidationError as e:
                logger.warning(f"JSON Validation failed (attempt {attempt+1}/{retries}): {e}")
                if attempt + 1 >= retries: 
                    raise LLMError(f"Invalid JSON after {retries} attempts: {e}") from e
                
                # Feedback the error to the LLM for the next attempt
                messages.append({"role": "assistant", "content": response_content})
                messages.append({
                    "role": "user", 
                    "content": f"Your last response failed JSON validation:\n{str(e)}\n\nPlease FIX the error and respond with the correct JSON object."
                })
