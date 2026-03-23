from __future__ import annotations

import pytest

from dslighting.ops.llm.basic import LLMBasedReviewOperator
from dslighting.core.types import ReviewResult


class _FakeLLMService:
    def __init__(self) -> None:
        self.prompt: str | None = None

    async def call_with_json(self, prompt: str, output_model):
        self.prompt = prompt
        return output_model(
            is_buggy=False,
            summary="ok",
            metric_value=0.91,
            lower_is_better=False,
        )


@pytest.mark.asyncio
async def test_review_operator_uses_grounded_metric_and_explicit_direction() -> None:
    fake_llm = _FakeLLMService()
    operator = LLMBasedReviewOperator(llm_service=fake_llm)

    result = await operator(
        prompt_context={
            "task": {
                "goal_and_data": "Predict demand",
                "metric_name": "score",
                "lower_is_better": False,
            },
            "code": "print('done')",
            "output": "finished",
            "grounded_metric_value": 0.91,
        }
    )

    assert isinstance(result, ReviewResult)
    assert fake_llm.prompt is not None
    assert "authoritative grounded metric" in fake_llm.prompt
    assert "Set `metric_value` to this exact numeric value" in fake_llm.prompt
    assert "Set `lower_is_better` to false" in fake_llm.prompt


@pytest.mark.asyncio
async def test_review_operator_allows_null_direction_when_unknown() -> None:
    fake_llm = _FakeLLMService()
    operator = LLMBasedReviewOperator(llm_service=fake_llm)

    await operator(
        prompt_context={
            "task": {"goal_and_data": "Summarize results"},
            "code": "print('accuracy: 0.5')",
            "output": "accuracy: 0.5",
        }
    )

    assert fake_llm.prompt is not None
    assert "otherwise set it to null" in fake_llm.prompt
