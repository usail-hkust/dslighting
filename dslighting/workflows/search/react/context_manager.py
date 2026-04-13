"""Context management and budget enforcement for the ReAct workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Optional

from dslighting.state.context import (
    DEFAULT_MAX_HISTORY_CHARS,
    DEFAULT_MAX_OUTPUT_CHARS,
    hard_truncate_chars,
    hard_truncate_head_tail,
)
from dslighting.core.config.runtime_params import (
    AGENT_RUNTIME_CONTEXT_ALLOWED_KEYS,
    AGENT_RUNTIME_CONTEXT_ALLOWED_STRATEGIES,
    normalize_agent_runtime_context_params,
)
from dslighting.workflows.search.react.validation import validate_react_operator_params

logger = logging.getLogger(__name__)

REACT_CONTEXT_ALLOWED_STRATEGIES = AGENT_RUNTIME_CONTEXT_ALLOWED_STRATEGIES
REACT_CONTEXT_ALLOWED_KEYS = AGENT_RUNTIME_CONTEXT_ALLOWED_KEYS

DEFAULT_REACT_CONTEXT = {
    "strategy": "hybrid",
    "max_history_chars": 48000,
    "keep_recent_turns": 14,
    "max_observation_chars": DEFAULT_MAX_OUTPUT_CHARS,
    "summary_trigger_turns": 18,
    "summary_max_chars": 4000,
    "keep_latest_feedback_only": True,
    "max_feedback_retries": 2,
    "recent_observation_window": 8,
    "max_feedback_chars": 1200,
}

_TAG_PATTERN_TEMPLATE = r"<{tag}>(.*?)</{tag}>"
_STRICT_PYTHON_BLOCK_PATTERN = re.compile(
    r"\s*```python\s*(?P<code>.*?)\s*```\s*",
    re.DOTALL | re.IGNORECASE,
)
_CRITICAL_SUBMISSION_STATUS_PATTERN = re.compile(
    r"<SubmissionStatus\b(?=[^>]*critical=[\"']true[\"'])[^>]*>.*?</SubmissionStatus>",
    re.DOTALL | re.IGNORECASE,
)

_SUMMARY_MIN_CHARS = 192
_TASK_MIN_CHARS = 256
_RUNTIME_COMPRESSED_MIN_CHARS = 320
_RUNTIME_COMPRESSED_MAX_CHARS = 1200
_SUMMARY_TAIL_TURNS = 6
_MASKED_OBSERVATION_TEXT = (
    "[Older execution output omitted from the prompt window. "
    "Consult the historical summary and saved full history for details.]"
)
_MASKED_RUNTIME_TEXT = (
    "[Older runtime content omitted from the prompt window. "
    "Consult the historical summary and saved full history for details.]"
)


def normalize_react_context_params(params: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Normalize nested context params from the shared agent_runtime config."""
    return normalize_agent_runtime_context_params(
        params,
        source="agent_runtime.context",
    )


@dataclass(frozen=True)
class ReActContextConfig:
    strategy: str = DEFAULT_REACT_CONTEXT["strategy"]
    max_history_chars: int = DEFAULT_REACT_CONTEXT["max_history_chars"]
    keep_recent_turns: int = DEFAULT_REACT_CONTEXT["keep_recent_turns"]
    max_observation_chars: int = DEFAULT_REACT_CONTEXT["max_observation_chars"]
    summary_trigger_turns: int = DEFAULT_REACT_CONTEXT["summary_trigger_turns"]
    summary_max_chars: int = DEFAULT_REACT_CONTEXT["summary_max_chars"]
    keep_latest_feedback_only: bool = DEFAULT_REACT_CONTEXT["keep_latest_feedback_only"]
    max_feedback_retries: int = DEFAULT_REACT_CONTEXT["max_feedback_retries"]
    recent_observation_window: int = DEFAULT_REACT_CONTEXT["recent_observation_window"]
    max_feedback_chars: int = DEFAULT_REACT_CONTEXT["max_feedback_chars"]


def validate_react_context_config(config: ReActContextConfig) -> ReActContextConfig:
    """Validate cross-field ReAct context constraints."""
    if config.summary_trigger_turns < config.keep_recent_turns:
        raise ValueError("`context.summary_trigger_turns` must be >= `context.keep_recent_turns`")
    return config


def build_react_context_config(
    params: ReActContextConfig | dict[str, Any] | None,
) -> ReActContextConfig:
    if isinstance(params, ReActContextConfig):
        return validate_react_context_config(params)
    normalized = normalize_react_context_params(params)
    return validate_react_context_config(
        ReActContextConfig(**{**DEFAULT_REACT_CONTEXT, **normalized})
    )


@dataclass
class ReActTurn:
    assistant_reply: str
    runtime_reply: str | None = None
    runtime_kind: str | None = None


@dataclass
class _RenderedTurnState:
    turn: ReActTurn
    runtime_mode: str = "raw"


@dataclass
class _PromptWindowState:
    task_message: str
    summary_message: str | None = None
    rendered_turns: list[_RenderedTurnState] = field(default_factory=list)


class ReActContextManager:
    """Manage ReAct turn history and build bounded LLM message windows."""

    def __init__(
        self,
        *,
        system_prompt: str,
        task_message: str,
        config: ReActContextConfig | dict[str, Any] | None = None,
    ) -> None:
        self.system_message = {"role": "system", "content": system_prompt}
        self.task_message = {"role": "user", "content": task_message}
        self.config = (
            validate_react_context_config(config)
            if isinstance(config, ReActContextConfig)
            else build_react_context_config(config)
        )
        self.turns: list[ReActTurn] = []

    def add_assistant_reply(self, content: str) -> None:
        self.turns.append(ReActTurn(assistant_reply=content))

    def add_runtime_reply(self, content: str) -> None:
        if not self.turns:
            raise ValueError("Cannot append runtime reply before an assistant turn.")
        self.turns[-1].runtime_reply = content
        self.turns[-1].runtime_kind = self._detect_runtime_kind(content)

    def export_full_history(self) -> list[dict[str, str]]:
        messages = [self.system_message, self.task_message]
        for turn in self.turns:
            messages.append({"role": "assistant", "content": turn.assistant_reply})
            if turn.runtime_reply is not None:
                messages.append({"role": "user", "content": turn.runtime_reply})
        return messages

    def build_messages(self) -> list[dict[str, str]]:
        if not self.turns:
            return [self.system_message, self.task_message]

        state = self._build_prompt_window()
        return self._fit_window_to_budget(state)

    def consecutive_feedback_turns(self) -> int:
        count = 0
        for turn in reversed(self.turns):
            if turn.runtime_kind == "feedback":
                count += 1
                continue
            if turn.runtime_kind == "observation":
                break
        return count

    def _build_prompt_window(self) -> _PromptWindowState:
        if self.config.strategy == "recent_turns":
            recent_turns = self._select_recent_turns(self.turns)
            return _PromptWindowState(
                task_message=self.task_message["content"],
                rendered_turns=self._build_rendered_turns(recent_turns),
            )

        if self.config.strategy == "summarize_old_turns":
            return self._build_summary_window()

        return self._build_hybrid_window()

    def _build_summary_window(self) -> _PromptWindowState:
        older_turns, recent_turns = self._partition_turns(self.turns)
        summary = self._build_summary_message(older_turns) if older_turns else None
        return _PromptWindowState(
            task_message=self.task_message["content"],
            summary_message=summary,
            rendered_turns=self._build_rendered_turns(
                self._filter_recent_feedback_turns(recent_turns)
            ),
        )

    def _build_hybrid_window(self) -> _PromptWindowState:
        if len(self.turns) <= self.config.keep_recent_turns:
            return _PromptWindowState(
                task_message=self.task_message["content"],
                rendered_turns=self._build_rendered_turns(
                    self._filter_recent_feedback_turns(self.turns)
                ),
            )

        if len(self.turns) < self.config.summary_trigger_turns:
            recent_turns = self._select_recent_turns(self.turns)
            return _PromptWindowState(
                task_message=self.task_message["content"],
                rendered_turns=self._build_rendered_turns(recent_turns),
            )

        return self._build_summary_window()

    def _build_rendered_turns(self, turns: list[ReActTurn]) -> list[_RenderedTurnState]:
        observation_indexes = [
            idx
            for idx, turn in enumerate(turns)
            if turn.runtime_kind == "observation" and turn.runtime_reply is not None
        ]
        raw_observation_indexes = set(observation_indexes[-self.config.recent_observation_window :])

        rendered: list[_RenderedTurnState] = []
        for idx, turn in enumerate(turns):
            runtime_mode = "raw"
            if turn.runtime_reply is None:
                runtime_mode = "none"
            elif turn.runtime_kind == "observation" and idx not in raw_observation_indexes:
                runtime_mode = "compressed"
            rendered.append(
                _RenderedTurnState(
                    turn=turn,
                    runtime_mode=runtime_mode,
                )
            )
        return rendered

    def _fit_window_to_budget(self, state: _PromptWindowState) -> list[dict[str, str]]:
        previous_total = None

        while True:
            messages = self._render_prompt_window(state)
            total_chars = self._message_chars(messages)
            if total_chars <= self.config.max_history_chars:
                return messages

            if previous_total is not None and total_chars >= previous_total:
                logger.warning(
                    "[ReActContextManager] prompt window did not shrink further; "
                    "falling back to strict message-level truncation."
                )
                return self._truncate_messages_to_budget(messages)

            previous_total = total_chars
            overflow = total_chars - self.config.max_history_chars

            if self._shrink_summary(state, overflow):
                continue
            if self._degrade_oldest_recent_runtime(state):
                continue
            if self._drop_oldest_recent_turn(state):
                continue
            if self._shrink_task_message(state, overflow):
                continue

            logger.warning(
                "[ReActContextManager] prompt window exhausted structured shrink "
                "strategies; applying strict message-level truncation."
            )
            return self._truncate_messages_to_budget(messages)

    def _render_prompt_window(self, state: _PromptWindowState) -> list[dict[str, str]]:
        messages = [
            self.system_message,
            {"role": "user", "content": state.task_message},
        ]
        if state.summary_message:
            messages.append({"role": "user", "content": state.summary_message})
        for rendered_turn in state.rendered_turns:
            messages.extend(
                self._render_turn_messages(
                    rendered_turn.turn,
                    runtime_mode=rendered_turn.runtime_mode,
                )
            )
        return messages

    def _shrink_summary(self, state: _PromptWindowState, overflow: int) -> bool:
        if not state.summary_message:
            return False

        current = state.summary_message
        min_chars = min(_SUMMARY_MIN_CHARS, self.config.summary_max_chars)
        if len(current) <= min_chars:
            return False

        target = max(min_chars, len(current) - overflow)
        updated = hard_truncate_chars(
            current,
            target,
            marker_template="\n...[SUMMARY TRUNCATED {omitted} chars]...\n",
        )
        if len(updated) < len(current):
            state.summary_message = updated
            return True
        return False

    def _degrade_oldest_recent_runtime(self, state: _PromptWindowState) -> bool:
        for rendered_turn in state.rendered_turns:
            turn = rendered_turn.turn
            if turn.runtime_reply is None or turn.runtime_kind == "feedback":
                continue

            current_content = self._render_runtime_for_history(
                turn,
                mode=rendered_turn.runtime_mode,
            )
            for next_mode in self._next_runtime_modes(rendered_turn.runtime_mode):
                candidate = self._render_runtime_for_history(turn, mode=next_mode)
                if len(candidate) < len(current_content):
                    rendered_turn.runtime_mode = next_mode
                    return True
        return False

    @staticmethod
    def _next_runtime_modes(mode: str) -> tuple[str, ...]:
        if mode == "raw":
            return ("compressed", "masked")
        if mode == "compressed":
            return ("masked",)
        return ()

    def _drop_oldest_recent_turn(self, state: _PromptWindowState) -> bool:
        if len(state.rendered_turns) <= 1:
            return False

        dropped = state.rendered_turns.pop(0)
        logger.info(
            "[ReActContextManager] dropping oldest raw turn from LLM window | " "runtime_kind=%s",
            dropped.turn.runtime_kind or "none",
        )
        return True

    def _shrink_task_message(self, state: _PromptWindowState, overflow: int) -> bool:
        current = state.task_message
        min_chars = min(_TASK_MIN_CHARS, max(64, self.config.max_history_chars // 4))
        if len(current) <= min_chars:
            return False

        target = max(min_chars, len(current) - overflow)
        updated = hard_truncate_chars(
            current,
            target,
            marker_template="\n...[TASK TRUNCATED {omitted} chars]...\n",
        )
        if len(updated) < len(current):
            state.task_message = updated
            return True
        return False

    def _truncate_messages_to_budget(
        self,
        messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        trimmed = [dict(message) for message in messages]
        total_chars = self._message_chars(trimmed)
        if total_chars <= self.config.max_history_chars:
            return trimmed

        while total_chars > self.config.max_history_chars:
            changed = False
            for idx in range(len(trimmed) - 1, 1, -1):
                content = trimmed[idx]["content"]
                if len(content) <= 128:
                    continue
                overflow = total_chars - self.config.max_history_chars
                target = max(128, len(content) - overflow)
                updated = self._truncate_message_content(
                    content,
                    target,
                    marker_template="\n...[PROMPT TRUNCATED {omitted} chars]...\n",
                )
                if len(updated) < len(content):
                    trimmed[idx]["content"] = updated
                    total_chars = self._message_chars(trimmed)
                    changed = True
                    if total_chars <= self.config.max_history_chars:
                        break
            if changed:
                continue

            for idx in (1, 0):
                content = trimmed[idx]["content"]
                if len(content) <= 64:
                    continue
                overflow = total_chars - self.config.max_history_chars
                target = max(64, len(content) - overflow)
                updated = self._truncate_message_content(
                    content,
                    target,
                    marker_template="\n...[PROMPT TRUNCATED {omitted} chars]...\n",
                )
                if len(updated) < len(content):
                    trimmed[idx]["content"] = updated
                    total_chars = self._message_chars(trimmed)
                    changed = True
                    if total_chars <= self.config.max_history_chars:
                        break

            if not changed:
                logger.warning(
                    "[ReActContextManager] message-level truncation could not reduce "
                    "the prompt further; returning the smallest safe window assembled."
                )
                break

        return trimmed

    def _truncate_message_content(
        self,
        content: str,
        max_chars: int,
        *,
        marker_template: str,
    ) -> str:
        match = _CRITICAL_SUBMISSION_STATUS_PATTERN.search(content)
        if match is None:
            return hard_truncate_chars(
                content,
                max_chars,
                marker_template=marker_template,
            )

        footer = match.group(0).strip()
        body = (content[: match.start()] + content[match.end() :]).strip()
        if len(footer) >= max_chars:
            raise ValueError(
                "Critical SubmissionStatus footer exceeds the prompt window budget; "
                "shorten the output contract status renderer or increase "
                "`agent_runtime.context.max_history_chars`."
            )
        truncated_body = hard_truncate_chars(
            body,
            max_chars - len(footer) - 1,
            marker_template=marker_template,
        )
        if truncated_body:
            return f"{truncated_body}\n{footer}"
        return footer

    def _partition_turns(self, turns: list[ReActTurn]) -> tuple[list[ReActTurn], list[ReActTurn]]:
        recent_raw = turns[-self.config.keep_recent_turns :]
        older = turns[: len(turns) - len(recent_raw)]
        return older, recent_raw

    def _select_recent_turns(self, turns: list[ReActTurn]) -> list[ReActTurn]:
        return self._filter_recent_feedback_turns(turns[-self.config.keep_recent_turns :])

    def _filter_recent_feedback_turns(self, turns: list[ReActTurn]) -> list[ReActTurn]:
        if not self.config.keep_latest_feedback_only:
            return list(turns)

        latest_feedback_idx = None
        for idx, turn in enumerate(turns):
            if turn.runtime_kind == "feedback":
                latest_feedback_idx = idx

        if latest_feedback_idx is None:
            return list(turns)

        filtered: list[ReActTurn] = []
        for idx, turn in enumerate(turns):
            if turn.runtime_kind == "feedback" and idx != latest_feedback_idx:
                continue
            filtered.append(turn)
        return filtered

    def _build_summary_message(self, turns: list[ReActTurn]) -> str | None:
        if not turns:
            return None

        return hard_truncate_chars(
            self._build_structured_summary(turns),
            self.config.summary_max_chars,
            marker_template="\n...[SUMMARY TRUNCATED {omitted} chars]...\n",
        )

    def _build_structured_summary(self, turns: list[ReActTurn]) -> str:
        observation_turns = [
            turn for turn in turns if turn.runtime_kind == "observation" and turn.runtime_reply
        ]
        feedback_turns = [
            turn for turn in turns if turn.runtime_kind == "feedback" and turn.runtime_reply
        ]
        last_observation = (
            self._extract_runtime_inner(
                observation_turns[-1].runtime_reply or "",
                "observation",
            )
            if observation_turns
            else None
        )
        last_feedback = (
            self._extract_runtime_inner(
                feedback_turns[-1].runtime_reply or "",
                "feedback",
            )
            if feedback_turns
            else None
        )

        lines = [
            "Historical State Summary",
            f"- Older turns condensed: {len(turns)}",
            f"- Successful execution observations: {len(observation_turns)}",
            f"- Protocol feedback turns: {len(feedback_turns)}",
            "- Last older successful observation: "
            + (self._shorten(last_observation, 180) if last_observation else "none"),
            "- Last older protocol feedback: "
            + (self._shorten(last_feedback, 160) if last_feedback else "none"),
            "- Condensed older turn log:",
        ]

        start_index = max(0, len(turns) - _SUMMARY_TAIL_TURNS)
        for offset, turn in enumerate(turns[start_index:], start=start_index + 1):
            lines.append(f"  - Turn {offset}: {self._summarize_turn(turn)}")

        return "\n".join(lines)

    def _summarize_turn(self, turn: ReActTurn) -> str:
        think = self._extract_tag_content(turn.assistant_reply, "Think")
        action = self._extract_tag_content(turn.assistant_reply, "Action")
        parts: list[str] = []

        if think:
            parts.append(f"think={self._shorten(think, 96)}")

        if action:
            if _STRICT_PYTHON_BLOCK_PATTERN.fullmatch(action):
                parts.append("action=executed python code")
            else:
                parts.append(f"action={self._shorten(action, 120)}")
        else:
            parts.append("action=malformed assistant reply")

        if turn.runtime_reply:
            runtime_inner = self._extract_runtime_inner(turn.runtime_reply, turn.runtime_kind)
            label = turn.runtime_kind or "runtime"
            parts.append(f"{label}={self._shorten(runtime_inner, 140)}")

        return "; ".join(parts)

    def _render_turn_messages(
        self,
        turn: ReActTurn,
        *,
        runtime_mode: str,
    ) -> list[dict[str, str]]:
        messages = [{"role": "assistant", "content": turn.assistant_reply}]
        if turn.runtime_reply is not None and runtime_mode != "none":
            messages.append(
                {
                    "role": "user",
                    "content": self._render_runtime_for_history(
                        turn,
                        mode=runtime_mode,
                    ),
                }
            )
        return messages

    def _render_runtime_for_history(self, turn: ReActTurn, *, mode: str = "raw") -> str:
        if turn.runtime_reply is None:
            return ""

        if mode == "masked":
            if turn.runtime_kind == "observation":
                return f"<Observation>\n{_MASKED_OBSERVATION_TEXT}\n</Observation>"
            return hard_truncate_chars(_MASKED_RUNTIME_TEXT, 160)

        if turn.runtime_kind == "observation":
            inner = self._extract_runtime_inner(turn.runtime_reply, "observation")
            budget = (
                self.config.max_observation_chars
                if mode == "raw"
                else self._compressed_runtime_budget()
            )
            inner = self._truncate_preserving_critical_submission_status(
                inner,
                budget,
                marker_template="\n...[OBSERVATION TRUNCATED {omitted} chars]...\n",
            )
            return f"<Observation>\n{inner}\n</Observation>"

        if turn.runtime_kind == "feedback":
            inner = self._extract_runtime_inner(turn.runtime_reply, "feedback")
            inner = hard_truncate_chars(
                inner,
                self.config.max_feedback_chars,
                marker_template="\n...[FEEDBACK TRUNCATED {omitted} chars]...\n",
            )
            return f"<Feedback>\n{inner}\n</Feedback>"

        budget = (
            self.config.max_observation_chars
            if mode == "raw"
            else self._compressed_runtime_budget()
        )
        return hard_truncate_head_tail(
            turn.runtime_reply,
            budget,
            marker_template="\n...[RUNTIME TRUNCATED {omitted} chars]...\n",
        )

    def _truncate_preserving_critical_submission_status(
        self,
        content: str,
        max_chars: int,
        *,
        marker_template: str,
    ) -> str:
        match = _CRITICAL_SUBMISSION_STATUS_PATTERN.search(content)
        if match is None:
            return hard_truncate_head_tail(
                content,
                max_chars,
                marker_template=marker_template,
            )

        footer = match.group(0).strip()
        body = (content[: match.start()] + content[match.end() :]).strip()
        if len(footer) >= max_chars:
            raise ValueError(
                "Critical SubmissionStatus footer exceeds "
                "`agent_runtime.context.max_observation_chars`; shorten the "
                "output contract status renderer or increase the context budget."
            )

        body_budget = max_chars - len(footer) - 1
        truncated_body = hard_truncate_head_tail(
            body,
            body_budget,
            marker_template=marker_template,
        )
        if truncated_body:
            return f"{truncated_body}\n{footer}"
        return footer

    def _compressed_runtime_budget(self) -> int:
        return min(
            _RUNTIME_COMPRESSED_MAX_CHARS,
            max(_RUNTIME_COMPRESSED_MIN_CHARS, self.config.max_observation_chars // 3),
        )

    @staticmethod
    def _detect_runtime_kind(content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("<Observation>"):
            return "observation"
        if stripped.startswith("<Feedback>"):
            return "feedback"
        return "runtime"

    @staticmethod
    def _extract_tag_content(content: str, tag: str) -> Optional[str]:
        match = re.search(_TAG_PATTERN_TEMPLATE.format(tag=tag), content, re.DOTALL)
        if not match:
            return None
        return match.group(1).strip()

    def _extract_runtime_inner(self, content: str, runtime_kind: str | None) -> str:
        tag = "Observation" if runtime_kind == "observation" else "Feedback"
        return self._extract_tag_content(content, tag) or content.strip()

    @staticmethod
    def _message_chars(messages: list[dict[str, str]]) -> int:
        return sum(len(message.get("content", "") or "") for message in messages)

    @staticmethod
    def _shorten(text: str | None, max_chars: int) -> str:
        compact = " ".join((text or "").split())
        if len(compact) <= max_chars:
            return compact
        return compact[: max_chars - 3] + "..."


__all__ = [
    "DEFAULT_REACT_CONTEXT",
    "REACT_CONTEXT_ALLOWED_KEYS",
    "REACT_CONTEXT_ALLOWED_STRATEGIES",
    "ReActContextConfig",
    "ReActContextManager",
    "ReActTurn",
    "build_react_context_config",
    "normalize_react_context_params",
    "validate_react_context_config",
    "validate_react_operator_params",
]
