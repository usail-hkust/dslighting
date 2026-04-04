from __future__ import annotations

import pytest

from dslighting.workflows.search.react_context_manager import (
    ReActContextConfig,
    ReActContextManager,
    build_react_context_config,
)


def _assistant_turn(index: int) -> str:
    return (
        f"<Think>reason {index}</Think>"
        f"<Action>```python\nprint('turn-{index}')\n```</Action>"
    )


def _observation_turn(index: int, *, extra: str = "") -> str:
    body = f"observation {index}"
    if extra:
        body = f"{body} {extra}"
    return f"<Observation>\n{body}\n</Observation>"


def _feedback_turn(index: int) -> str:
    return f"<Feedback>\nProtocol error {index}\n</Feedback>"


def _build_manager(config: ReActContextConfig) -> ReActContextManager:
    return ReActContextManager(
        system_prompt="system prompt",
        task_message="task prompt",
        config=config,
    )


def test_recent_turns_strategy_keeps_only_latest_raw_turns() -> None:
    manager = _build_manager(
        ReActContextConfig(
            strategy="recent_turns",
            keep_recent_turns=2,
            max_history_chars=4000,
        )
    )

    for idx in range(1, 5):
        manager.add_assistant_reply(_assistant_turn(idx))
        manager.add_runtime_reply(_observation_turn(idx))

    messages = manager.build_messages()
    payload = "\n".join(message["content"] for message in messages)

    assert len(messages) == 6
    assert "turn-1" not in payload
    assert "turn-2" not in payload
    assert "turn-3" in payload
    assert "turn-4" in payload


def test_summarize_old_turns_strategy_inserts_structured_summary() -> None:
    manager = _build_manager(
        ReActContextConfig(
            strategy="summarize_old_turns",
            keep_recent_turns=2,
            max_history_chars=4000,
            summary_max_chars=1200,
        )
    )

    for idx in range(1, 5):
        manager.add_assistant_reply(_assistant_turn(idx))
        manager.add_runtime_reply(_observation_turn(idx))

    messages = manager.build_messages()
    payload = "\n".join(message["content"] for message in messages)

    assert any("Historical State Summary" in message["content"] for message in messages)
    assert "Successful execution observations" in payload
    assert "turn-1" not in [
        message["content"] for message in messages if message["role"] == "assistant"
    ]
    assert "turn-3" in payload
    assert "turn-4" in payload


def test_hybrid_strategy_summary_shrink_is_strict_and_terminates() -> None:
    manager = _build_manager(
        ReActContextConfig(
            strategy="hybrid",
            keep_recent_turns=2,
            summary_trigger_turns=3,
            max_history_chars=1200,
            summary_max_chars=1500,
            max_observation_chars=300,
            recent_observation_window=1,
        )
    )

    for idx in range(1, 7):
        manager.add_assistant_reply(_assistant_turn(idx))
        manager.add_runtime_reply(_observation_turn(idx, extra="X" * 220))

    messages = manager.build_messages()
    payload = "\n".join(message["content"] for message in messages)

    assert sum(len(message["content"]) for message in messages) <= 1200
    assert any("Historical State Summary" in message["content"] for message in messages)
    assert "turn-6" in payload
    assert "turn-1" not in [
        message["content"] for message in messages if message["role"] == "assistant"
    ]


def test_context_manager_keeps_only_latest_feedback_turn_in_raw_window() -> None:
    manager = _build_manager(
        ReActContextConfig(
            strategy="recent_turns",
            keep_recent_turns=4,
            max_history_chars=4000,
            keep_latest_feedback_only=True,
        )
    )

    manager.add_assistant_reply(_assistant_turn(1))
    manager.add_runtime_reply(_feedback_turn(1))
    manager.add_assistant_reply(_assistant_turn(2))
    manager.add_runtime_reply(_feedback_turn(2))
    manager.add_assistant_reply(_assistant_turn(3))
    manager.add_runtime_reply(_observation_turn(3))

    messages = manager.build_messages()
    payload = "\n".join(message["content"] for message in messages)

    assert "Protocol error 1" not in payload
    assert "Protocol error 2" in payload
    assert manager.consecutive_feedback_turns() == 0


def test_context_manager_compresses_older_recent_observations() -> None:
    manager = _build_manager(
        ReActContextConfig(
            strategy="recent_turns",
            keep_recent_turns=4,
            max_history_chars=5000,
            max_observation_chars=240,
            recent_observation_window=1,
        )
    )

    for idx in range(1, 5):
        extra = ("head-" + str(idx) + " ") + ("X" * 720) + (" tail-" + str(idx))
        manager.add_assistant_reply(_assistant_turn(idx))
        manager.add_runtime_reply(_observation_turn(idx, extra=extra))

    messages = manager.build_messages()
    observation_messages = [
        message["content"]
        for message in messages
        if message["role"] == "user" and message["content"].startswith("<Observation>")
    ]

    assert len(observation_messages) == 4
    assert any("OBSERVATION TRUNCATED" in message for message in observation_messages[:-1])
    assert "tail-4" in observation_messages[-1]


def test_context_manager_strict_budget_truncation_makes_progress() -> None:
    manager = _build_manager(
        ReActContextConfig(
            strategy="recent_turns",
            keep_recent_turns=1,
            max_history_chars=420,
        )
    )

    manager.add_assistant_reply(
        "<Think>" + ("A" * 180) + "</Think><Action>done</Action>"
    )
    manager.add_runtime_reply(
        "<Observation>\n" + ("B" * 180) + "\n</Observation>"
    )

    messages = manager.build_messages()

    assert sum(len(message["content"]) for message in messages) <= 420


def test_build_react_context_config_rejects_invalid_relationships() -> None:
    with pytest.raises(ValueError, match="summary_trigger_turns"):
        build_react_context_config(
            {
                "keep_recent_turns": 2,
                "summary_trigger_turns": 1,
            }
        )
