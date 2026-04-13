"""Protocol helpers for the strict ReAct workflow."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from dslighting.utils.typing import ExecutionResult


@dataclass(frozen=True)
class NormalizedReActReply:
    """Normalized assistant reply plus repair metadata."""

    raw_content: str
    normalized_content: str
    repaired: bool = False
    repair_reason: str | None = None


@dataclass(frozen=True)
class ReActTurnResult:
    """Parsed outcome of one assistant reply in the ReAct protocol."""

    next_user_message: str | None = None
    final_answer: str | None = None
    execution_succeeded: bool = False
    action_code: str | None = None


_ACTION_TURN_PATTERN = re.compile(
    r"\s*<Think>(?P<think>.*?)</Think>\s*<Action>(?P<action>.*?)</Action>\s*",
    re.DOTALL,
)
_ANSWER_TURN_PATTERN = re.compile(
    r"\s*<Think>(?P<think>.*?)</Think>\s*<Answer>(?P<answer>.*?)</Answer>\s*",
    re.DOTALL,
)
_UNCLOSED_ANSWER_TURN_PATTERN = re.compile(
    r"\s*<Think>(?P<think>.*?)</Think>\s*<Answer>(?P<answer>.*)",
    re.DOTALL,
)
_STRICT_PYTHON_BLOCK_PATTERN = re.compile(
    r"\s*```python\s*(?P<code>.*?)\s*```\s*",
    re.DOTALL | re.IGNORECASE,
)


def parse_react_reply(content: str) -> ReActTurnResult:
    """Parse one assistant reply into either code, a final answer, or protocol feedback."""
    normalized = normalize_react_reply(content)
    is_valid, reason = validate_turn_structure(normalized.normalized_content)
    if not is_valid:
        return ReActTurnResult(
            next_user_message=wrap_feedback(build_protocol_error_feedback(reason))
        )

    action = extract_action_block(normalized.normalized_content)
    if action is not None:
        code = extract_strict_python_from_action(action)
        if code is not None:
            return ReActTurnResult(action_code=code)

        final_answer = extract_final_answer_from_action(action)
        if final_answer is None:
            return ReActTurnResult(
                next_user_message=wrap_feedback(
                    build_protocol_error_feedback(
                        "Code actions must contain exactly one fenced ```python``` block "
                        "with no extra text before or after it."
                    )
                )
            )
        return ReActTurnResult(final_answer=final_answer)

    answer = extract_answer_block(normalized.normalized_content)
    if answer is None:
        return ReActTurnResult(
            next_user_message=wrap_feedback(
                build_protocol_error_feedback(
                    "Missing <Action>...</Action> or <Answer>...</Answer> block."
                )
            )
        )
    return ReActTurnResult(final_answer=answer)


def build_execution_message(
    exec_result: ExecutionResult,
    *,
    obs_max_tokens: int,
    obs_head_tokens: int,
    obs_tail_tokens: int,
    critical_footer: str | None = None,
) -> str:
    """Render execution output back into the ReAct conversation."""
    execution_output = truncate_observation(
        format_observation(exec_result),
        obs_max_tokens=obs_max_tokens,
        obs_head_tokens=obs_head_tokens,
        obs_tail_tokens=obs_tail_tokens,
    )
    if critical_footer:
        observation = (
            "<ExecutionOutput>\n"
            f"{execution_output}\n"
            "</ExecutionOutput>\n"
            f"{critical_footer.strip()}"
        )
    else:
        observation = execution_output
    return wrap_observation(observation)


def normalize_react_reply(content: str) -> NormalizedReActReply:
    """Repair only low-risk protocol shell issues for assistant replies."""
    raw_content = content if isinstance(content, str) else str(content)

    if "<Final Answer>" in raw_content or "</Final Answer>" in raw_content:
        return NormalizedReActReply(
            raw_content=raw_content,
            normalized_content=raw_content,
        )

    if _can_repair_unclosed_answer(raw_content):
        return NormalizedReActReply(
            raw_content=raw_content,
            normalized_content=raw_content.rstrip() + "\n</Answer>",
            repaired=True,
            repair_reason="added missing </Answer> closing tag",
        )

    return NormalizedReActReply(
        raw_content=raw_content,
        normalized_content=raw_content,
    )


def extract_tag_block(content: str, tag: str) -> Optional[str]:
    pattern = re.compile(rf"<{tag}>(.*?)</{tag}>", re.DOTALL)
    match = pattern.search(content)
    if not match:
        return None
    return match.group(1).strip()


def extract_think_block(content: str) -> Optional[str]:
    return extract_tag_block(content, "Think")


def extract_action_block(content: str) -> Optional[str]:
    return extract_tag_block(content, "Action")


def extract_answer_block(content: str) -> Optional[str]:
    return extract_tag_block(content, "Answer")


def extract_strict_python_from_action(action: str) -> Optional[str]:
    match = _STRICT_PYTHON_BLOCK_PATTERN.fullmatch(action)
    if not match:
        return None
    return match.group("code").strip()


def extract_final_answer_from_action(action: str) -> Optional[str]:
    stripped = action.strip()
    if not stripped or "```" in stripped:
        return None
    return stripped


def validate_turn_structure(content: str) -> tuple[bool, Optional[str]]:
    if "<Think>" not in content or "</Think>" not in content:
        return False, "Missing <Think>...</Think> block."

    if "<Final Answer>" in content or "</Final Answer>" in content:
        return (
            False,
            "<Final Answer>...</Final Answer> is not supported. Use <Answer>...</Answer> instead.",
        )

    has_action = "<Action>" in content or "</Action>" in content
    has_answer = "<Answer>" in content or "</Answer>" in content

    response_block_count = sum(1 for present in (has_action, has_answer) if present)
    if response_block_count == 0:
        return False, "Missing <Action>...</Action> or <Answer>...</Answer> block."
    if response_block_count > 1:
        return (
            False,
            "Reply must contain exactly one of <Action>...</Action> or <Answer>...</Answer>.",
        )

    think_index = content.find("<Think>")
    response_index = len(content)
    for tag in ("<Action>", "<Answer>"):
        index = content.find(tag)
        if index != -1:
            response_index = min(response_index, index)
    if think_index > response_index:
        return False, "<Think> must appear before <Action> or <Answer>."

    if has_action:
        match = _ACTION_TURN_PATTERN.fullmatch(content)
        if match is None:
            return (
                False,
                "Reply must contain only <Think>...</Think> followed by "
                "<Action>...</Action> with no extra text.",
            )
        think = match.group("think").strip()
        action = match.group("action").strip()
        if not think:
            return False, "<Think> cannot be empty."
        if not action:
            return False, "<Action> cannot be empty."
        return True, None

    if "<Answer>" in content and "</Answer>" not in content:
        return False, "Missing closing </Answer> tag."

    match = _ANSWER_TURN_PATTERN.fullmatch(content)
    if match is None:
        return (
            False,
            "Reply must contain only <Think>...</Think> followed by "
            "<Answer>...</Answer> with no extra text.",
        )
    think = match.group("think").strip()
    answer = match.group("answer").strip()
    if not think:
        return False, "<Think> cannot be empty."
    if not answer:
        return False, "<Answer> cannot be empty."
    if "```" in answer:
        return False, "<Answer> cannot contain a code block."
    return True, None


def _can_repair_unclosed_answer(content: str) -> bool:
    if "<Final Answer>" in content or "</Final Answer>" in content:
        return False
    if "<Action>" in content or "</Action>" in content:
        return False
    if content.count("<Answer>") != 1 or "</Answer>" in content:
        return False

    match = _UNCLOSED_ANSWER_TURN_PATTERN.fullmatch(content)
    if match is None:
        return False
    return bool(match.group("answer").strip())


def wrap_observation(observation: str) -> str:
    return f"<Observation>\n{observation}\n</Observation>"


def wrap_feedback(feedback: str) -> str:
    return f"<Feedback>\n{feedback}\n</Feedback>"


def build_protocol_error_feedback(reason: Optional[str]) -> str:
    detail = reason or "Malformed assistant reply."
    return (
        f"Protocol error: {detail}\n"
        "Reply using exactly:\n"
        "<Think>...</Think>\n"
        "<Action>...</Action>\n"
        "or:\n"
        "<Think>...</Think>\n"
        "<Answer>...</Answer>\n"
        "Always close every tag explicitly. In particular, finish completion replies with </Answer>.\n"
        "Use <Action> only for exactly one fenced ```python``` block. "
        "Use <Answer> only for plain-text completion after the task is done."
    )


def format_observation(exec_result: ExecutionResult) -> str:
    if exec_result.success:
        return exec_result.stdout or "(no output)"
    return exec_result.stderr or exec_result.stdout or "(execution failed with no output)"


def truncate_observation(
    text: str,
    *,
    obs_max_tokens: int,
    obs_head_tokens: int,
    obs_tail_tokens: int,
) -> str:
    """Keep at most obs_max_tokens tokens, preserving head and tail."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        if len(tokens) < obs_max_tokens:
            return text
        head = enc.decode(tokens[:obs_head_tokens])
        tail = enc.decode(tokens[-obs_tail_tokens:])
        return head + "\n...\n" + tail
    except Exception:
        max_chars = obs_max_tokens * 4
        if len(text) <= max_chars:
            return text
        half = max_chars // 2
        return text[:half] + "\n...\n" + text[-half:]


__all__ = [
    "NormalizedReActReply",
    "ReActTurnResult",
    "build_execution_message",
    "build_protocol_error_feedback",
    "extract_action_block",
    "extract_answer_block",
    "extract_final_answer_from_action",
    "extract_strict_python_from_action",
    "extract_think_block",
    "normalize_react_reply",
    "parse_react_reply",
    "truncate_observation",
    "validate_turn_structure",
    "wrap_feedback",
    "wrap_observation",
]
