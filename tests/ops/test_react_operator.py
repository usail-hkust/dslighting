from __future__ import annotations

import pytest

from dslighting.ops.presets.react import ReActOperator, ReActTurnResult
from dslighting.prompts.workflows.react import create_react_prompt
from dslighting.utils.typing import ExecutionResult


@pytest.mark.asyncio
async def test_react_operator_extracts_strict_python_action_for_workflow_execution() -> None:
    operator = ReActOperator(
        max_steps=3,
        obs_max_tokens=200,
        obs_head_tokens=100,
        obs_tail_tokens=100,
    )

    result = await operator(
        "<Think>Inspect the data.</Think>\n"
        "<Action>```python\nprint('hello')\n```</Action>",
    )

    assert isinstance(result, ReActTurnResult)
    assert result.final_answer is None
    assert result.execution_succeeded is False
    assert result.next_user_message is None
    assert result.action_code == "print('hello')"

    system_prompt = create_react_prompt(
        {
            "goal_and_data": "Predict the target.",
            "io_instructions": "Write submission.csv.",
        },
        output_filename="submission.csv",
    )
    assert "Role:" in system_prompt
    assert "Task Goal and Data Overview:" in system_prompt
    assert "CRITICAL I/O REQUIREMENTS (MUST BE FOLLOWED):" in system_prompt
    assert "Response Format:" in system_prompt
    assert "Action Semantics:" in system_prompt
    assert "<Feedback>...</Feedback>" in system_prompt
    assert "<Answer>...</Answer>" in system_prompt
    assert "Never output <Final Answer>" in system_prompt
    assert "required artifact has already been created" not in system_prompt
    assert "exact filename `submission.csv`" not in system_prompt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_reply",
    [
        "<Action>```python\nprint('oops')\n```</Action><Think>late</Think>",
        "<Think>Reason.</Think><Action>Before\n```python\nprint('oops')\n```\nAfter</Action>",
        "<Think>Reason.</Think><Action>```python\nprint('ok')\n```</Action><Answer>done</Answer>",
    ],
)
async def test_react_operator_rejects_malformed_turns(invalid_reply: str) -> None:
    operator = ReActOperator(
        max_steps=3,
        obs_max_tokens=200,
        obs_head_tokens=100,
        obs_tail_tokens=100,
    )

    result = await operator(invalid_reply)

    assert result.final_answer is None
    assert result.execution_succeeded is False
    assert result.next_user_message is not None
    assert result.action_code is None
    assert "Protocol error:" in result.next_user_message
    assert "<Feedback>" in result.next_user_message


@pytest.mark.asyncio
async def test_react_operator_returns_final_answer_for_answer_block() -> None:
    operator = ReActOperator()

    result = await operator("<Think>Done.</Think>\n<Answer>42</Answer>")

    assert result.final_answer == "42"
    assert result.next_user_message is None
    assert result.action_code is None
    assert result.execution_succeeded is False


@pytest.mark.asyncio
async def test_react_operator_repairs_unclosed_answer_block() -> None:
    operator = ReActOperator()

    result = await operator("<Think>Done.</Think>\n<Answer>42")

    assert result.final_answer == "42"
    assert result.next_user_message is None


@pytest.mark.asyncio
async def test_react_operator_rejects_legacy_final_answer_tag() -> None:
    operator = ReActOperator()

    result = await operator("<Think>Done.</Think>\n<Final Answer>42</Final Answer>")

    assert result.final_answer is None
    assert result.next_user_message is not None
    assert "<Final Answer>...</Final Answer> is not supported." in result.next_user_message


@pytest.mark.asyncio
async def test_react_operator_keeps_legacy_plain_text_action_as_compatibility_path() -> None:
    operator = ReActOperator()

    result = await operator("<Think>Done.</Think>\n<Action>42</Action>")

    assert result.final_answer == "42"
    assert result.next_user_message is None
    assert result.action_code is None
    assert result.execution_succeeded is False


@pytest.mark.asyncio
async def test_react_operator_formats_execution_observation_without_executing() -> None:
    operator = ReActOperator(obs_max_tokens=50, obs_head_tokens=25, obs_tail_tokens=25)

    message = operator.build_execution_message(
        ExecutionResult(success=True, stdout="hello world", stderr="")
    )

    assert message.startswith("<Observation>\n")
    assert "hello world" in message
    assert message.endswith("\n</Observation>")


def test_react_operator_rejects_invalid_observation_budget() -> None:
    with pytest.raises(ValueError, match="obs_head_tokens"):
        ReActOperator(
            obs_max_tokens=100,
            obs_head_tokens=60,
            obs_tail_tokens=60,
        )
