from __future__ import annotations

import json
from pathlib import Path

import pytest
import litellm.exceptions as litellm_exceptions
from pydantic import BaseModel

from dslighting.config import LLMConfig
from dslighting.debug.api import get_debug_session, init_debug
from dslighting.error import LLMServiceError
from dslighting.services.llm.pool import GlobalAPIKeyPool
from dslighting.services.llm.service import LLMService


class _OutputModel(BaseModel):
    value: str


class _Usage:
    prompt_tokens = 11
    completion_tokens = 7
    total_tokens = 18


class _Message:
    def __init__(self, content: str) -> None:
        self.role = "assistant"
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _Response:
    def __init__(self, content: str) -> None:
        self.choices = [_Choice(content)]
        self.usage = _Usage()

    def model_dump(self) -> dict:
        return {
            "choices": [{"message": {"role": "assistant", "content": self.choices[0].message.content}}],
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
            },
        }


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.mark.asyncio
async def test_call_with_json_emits_single_logical_call_with_validation_retry(monkeypatch, tmp_path: Path) -> None:
    GlobalAPIKeyPool.clear_pools()
    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)

    responses = iter([_Response('{"value": '), _Response('{"value": "ok"}')])

    async def _fake_acompletion(**kwargs):
        _ = kwargs
        return next(responses)

    monkeypatch.setattr("litellm.acompletion", _fake_acompletion)

    service = LLMService(LLMConfig(model="gpt-test", api_key="secret", api_base="https://example.com/v1"))
    try:
        result = await service.call_with_json("Return JSON", _OutputModel, max_retries=2)
        assert result.value == "ok"
    finally:
        current = get_debug_session()
        if current is not None:
            await current.close()

    assert session.output_dir is not None
    events = _load_jsonl(session.output_dir / "events.jsonl")
    payloads = _load_jsonl(session.output_dir / "payloads.jsonl")

    event_types = [entry["event_type"] for entry in events]
    assert "llm.call.started" in event_types
    assert "llm.request.prepared" in event_types
    assert "llm.response.received" in event_types
    assert "llm.validation.failed" in event_types
    assert "llm.retry.scheduled" in event_types
    assert "llm.call.completed" in event_types

    logical_call_ids = {entry["llm"]["logical_call_id"] for entry in events if entry.get("llm")}
    assert len(logical_call_ids) == 1

    request_payloads = [entry for entry in payloads if entry["kind"] == "request_messages"]
    assert len(request_payloads) == 1


@pytest.mark.asyncio
async def test_call_with_json_rotates_to_next_key_on_auth_failure(monkeypatch) -> None:
    GlobalAPIKeyPool.clear_pools()
    attempted_keys: list[str] = []

    async def _fake_acompletion(**kwargs):
        api_key = kwargs["api_key"]
        attempted_keys.append(api_key)
        if api_key == "bad-key":
            raise litellm_exceptions.AuthenticationError(
                message="Api key is invalid",
                llm_provider="openai",
                model="gpt-test",
            )
        return _Response('{"value": "ok"}')

    monkeypatch.setattr("litellm.acompletion", _fake_acompletion)

    service = LLMService(
        LLMConfig(
            model="gpt-test",
            api_keys=["bad-key", "good-key"],
            api_base="https://example.com/v1",
        )
    )
    result = await service.call_with_json("Return JSON", _OutputModel, max_retries=1)

    assert result.value == "ok"
    assert attempted_keys == ["bad-key", "good-key"]
    assert service._key_pool._last_error_kind["bad-key"] == "AuthenticationError"
    assert service._key_pool._cooldown_until["bad-key"] > 0.0


@pytest.mark.asyncio
async def test_call_with_json_fails_after_all_keys_auth_fail(monkeypatch) -> None:
    GlobalAPIKeyPool.clear_pools()
    attempted_keys: list[str] = []

    async def _fake_acompletion(**kwargs):
        api_key = kwargs["api_key"]
        attempted_keys.append(api_key)
        raise litellm_exceptions.AuthenticationError(
            message=f"Api key is invalid: {api_key}",
            llm_provider="openai",
            model="gpt-test",
        )

    monkeypatch.setattr("litellm.acompletion", _fake_acompletion)

    service = LLMService(
        LLMConfig(
            model="gpt-test",
            api_keys=["bad-key-1", "bad-key-2"],
            api_base="https://example.com/v1",
        )
    )

    with pytest.raises(LLMServiceError, match="exhausting 2 API key"):
        await service.call_with_json("Return JSON", _OutputModel, max_retries=1)

    assert attempted_keys == ["bad-key-1", "bad-key-2"]
