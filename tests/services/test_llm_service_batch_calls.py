from __future__ import annotations

import pytest
from pydantic import BaseModel

from dslighting.services.llm.service import LLMService


class _EchoModel(BaseModel):
    value: str


@pytest.mark.asyncio
async def test_batch_call_keeps_input_order() -> None:
    service = object.__new__(LLMService)

    async def _fake_call(prompt: str, system_message=None, max_retries=None) -> str:
        _ = system_message, max_retries
        return f"ok:{prompt}"

    service.call = _fake_call  # type: ignore[attr-defined]

    responses = await service.batch_call(["a", "b", "c"], batch_size=2)
    assert responses == ["ok:a", "ok:b", "ok:c"]


@pytest.mark.asyncio
async def test_batch_call_with_json_maps_failures_to_none() -> None:
    service = object.__new__(LLMService)

    async def _fake_call_with_json(prompt: str, output_model, max_retries=None):
        _ = max_retries
        if prompt == "bad":
            raise ValueError("bad prompt")
        return output_model(value=prompt)

    service.call_with_json = _fake_call_with_json  # type: ignore[attr-defined]

    responses = await service.batch_call_with_json(
        ["good", "bad", "good2"],
        output_model=_EchoModel,
        batch_size=2,
    )

    assert isinstance(responses[0], _EchoModel)
    assert responses[0].value == "good"
    assert responses[1] is None
    assert isinstance(responses[2], _EchoModel)
    assert responses[2].value == "good2"
