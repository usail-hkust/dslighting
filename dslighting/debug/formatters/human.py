"""Human-readable structured formatter for debug console output."""

from __future__ import annotations

import json
from typing import Any


class HumanStructuredFormatter:
    _RESET = "\033[0m"
    _BOLD = "\033[1m"
    _DIM = "\033[90m"
    _RED = "\033[91m"
    _GREEN = "\033[92m"
    _YELLOW = "\033[93m"
    _BLUE = "\033[94m"
    _CYAN = "\033[96m"

    def __init__(
        self,
        *,
        profile: str = "full",
        max_inline_chars: int = 12000,
        use_color: bool = True,
    ) -> None:
        self.profile = profile
        self.max_inline_chars = max_inline_chars
        self.use_color = use_color

    def format_call_block(
        self,
        events: list,
        payload_store,
        *,
        printed_payload_refs: set[str] | None = None,
    ) -> str:
        if printed_payload_refs is None:
            printed_payload_refs = set()
        if not events:
            return ""

        first = next((event for event in events if event.llm is not None), events[0])
        run = first.run
        node = first.node
        llm = first.llm
        status = "failed" if any(event.event_type == "llm.call.failed" for event in events) else "success"
        status_color = self._RED if status == "failed" else self._GREEN

        lines = [
            self._paint("[LLM]", self._CYAN, self._BOLD),
            "  "
            + " ".join(
                [
                    f"run={getattr(run, 'run_id', 'N/A')}",
                    f"task={getattr(run, 'task_id', 'N/A') or 'N/A'}",
                    f"workflow={getattr(run, 'workflow_name', 'N/A') or 'N/A'}",
                    f"node={getattr(node, 'node_id', 'N/A') or 'N/A'}",
                ]
            ),
            "  "
            + " ".join(
                [
                    f"call={getattr(llm, 'logical_call_id', 'N/A')[:12] if llm else 'N/A'}",
                    f"model={getattr(llm, 'model', 'N/A') if llm else 'N/A'}",
                    f"status={self._paint(status, status_color, self._BOLD)}",
                ]
            ),
        ]

        for event in events:
            lines.append("")
            llm_ctx = event.llm
            attempt_label = ""
            if llm_ctx is not None:
                attempt_label = (
                    f" [semantic={llm_ctx.semantic_attempt} transport={llm_ctx.transport_attempt}"
                    f" validation={llm_ctx.validation_attempt}]"
                )
            lines.append(
                f"- {self._paint(event.event_type, self._event_color(event.event_type), self._BOLD)}"
                f"{attempt_label}: {event.summary}"
            )

            lines.extend(self._render_standard_fields(event))

            for label, payload_ref in event.payload_refs.items():
                if payload_ref.ref in printed_payload_refs:
                    lines.append(
                        "  "
                        + f"{label}: payload={payload_ref.ref} reused"
                        + (f" preview={payload_ref.preview}" if payload_ref.preview else "")
                    )
                    continue
                printed_payload_refs.add(payload_ref.ref)
                lines.append(
                    f"  {label}: payload={payload_ref.ref} chars={payload_ref.chars_len} bytes={payload_ref.bytes_len}"
                )
                if self.profile != "summary":
                    payload = payload_store.get(payload_ref.ref)
                    lines.extend(self._render_payload(label=label, payload=payload))

        return "\n".join(lines)

    def _render_standard_fields(self, event) -> list[str]:
        lines: list[str] = []
        tags = dict(event.tags or {})
        metrics = dict(event.metrics or {})

        provider = tags.pop("provider", None)
        api_base = tags.pop("api_base", None)
        temperature = tags.pop("temperature", None)
        response_format = tags.pop("response_format", None)
        reason = tags.pop("reason", None)
        next_transport = tags.pop("next_transport_attempt", None)
        next_semantic = tags.pop("next_semantic_attempt", None)

        if provider is not None:
            lines.append(f"  Provider: {provider}")
        if api_base is not None:
            lines.append(f"  API Base: {api_base}")
        if temperature is not None:
            lines.append(f"  Temperature: {temperature}")
        if response_format is not None:
            lines.append(
                "  Response Format: "
                + json.dumps(response_format, ensure_ascii=False, sort_keys=True, default=str)
            )
        if reason is not None:
            lines.append(f"  Reason: {reason}")
        if next_transport is not None:
            lines.append(f"  Next Transport Attempt: {next_transport}")
        if next_semantic is not None:
            lines.append(f"  Next Semantic Attempt: {next_semantic}")

        duration = metrics.pop("duration_seconds", None)
        provider_duration = metrics.pop("provider_duration_seconds", None)
        if duration is not None:
            lines.append(f"  Duration: {duration:.4f}s" if isinstance(duration, float) else f"  Duration: {duration}s")
        if provider_duration is not None:
            lines.append(
                f"  Provider Duration: {provider_duration:.4f}s"
                if isinstance(provider_duration, float)
                else f"  Provider Duration: {provider_duration}s"
            )

        prompt_tokens = metrics.pop("prompt_tokens", None)
        completion_tokens = metrics.pop("completion_tokens", None)
        total_tokens = metrics.pop("total_tokens", None)
        message_count = metrics.pop("message_count", None)
        if message_count is not None:
            lines.append(f"  Message Count: {message_count}")
        if any(value is not None for value in (prompt_tokens, completion_tokens, total_tokens)):
            usage_parts = []
            if prompt_tokens is not None:
                usage_parts.append(f"prompt={prompt_tokens}")
            if completion_tokens is not None:
                usage_parts.append(f"completion={completion_tokens}")
            if total_tokens is not None:
                usage_parts.append(f"total={total_tokens}")
            lines.append("  Usage: " + " ".join(usage_parts))

        if tags:
            lines.append(f"  Tags: {json.dumps(tags, ensure_ascii=False, sort_keys=True, default=str)}")
        if metrics:
            lines.append(f"  Metrics: {json.dumps(metrics, ensure_ascii=False, sort_keys=True, default=str)}")
        if event.error:
            error_type = event.error.get("type")
            error_message = event.error.get("message")
            if error_type is not None:
                lines.append(f"  Error Type: {error_type}")
            if error_message is not None:
                lines.append(f"  Error Message: {error_message}")
            remaining = {
                key: value
                for key, value in event.error.items()
                if key not in {"type", "message"}
            }
            if remaining:
                lines.append(f"  Error: {json.dumps(remaining, ensure_ascii=False, sort_keys=True, default=str)}")
        return lines

    def _render_payload(self, *, label: str, payload: Any) -> list[str]:
        if label == "request_messages" and isinstance(payload, list):
            lines: list[str] = []
            for idx, item in enumerate(payload, start=1):
                role = "unknown"
                content = item
                if isinstance(item, dict):
                    role = str(item.get("role", "unknown"))
                    content = item.get("content", "")
                lines.append(f"    [{idx}] {role}:")
                lines.extend(self._indent_lines(self._stringify(content), prefix="      "))
            return lines
        if label.endswith("response_body") and isinstance(payload, dict):
            return self._render_response_payload(payload)
        return self._indent_lines(self._stringify(payload), prefix="    ")

    def _render_response_payload(self, payload: dict[str, Any]) -> list[str]:
        lines: list[str] = []
        choices = payload.get("choices")
        if isinstance(choices, list):
            for idx, choice in enumerate(choices, start=1):
                message = choice.get("message", {}) if isinstance(choice, dict) else {}
                role = message.get("role", "assistant")
                content = message.get("content", "")
                lines.append(f"    [{idx}] {role}:")
                lines.extend(self._indent_lines(self._stringify(content), prefix="      "))
        usage = payload.get("usage")
        if usage is not None:
            lines.append("    usage:")
            lines.extend(self._indent_lines(self._stringify(usage), prefix="      "))
        extra = {key: value for key, value in payload.items() if key not in {"choices", "usage"}}
        if extra:
            lines.append("    raw:")
            lines.extend(self._indent_lines(self._stringify(extra), prefix="      "))
        return lines or self._indent_lines(self._stringify(payload), prefix="    ")

    def _stringify(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)

    @staticmethod
    def _indent_lines(value: str, *, prefix: str) -> list[str]:
        return [f"{prefix}{line}" if line else prefix.rstrip() for line in value.splitlines() or [""]]

    def _event_color(self, event_type: str) -> str:
        if event_type.endswith("failed") or "failure" in event_type:
            return self._RED
        if "retry" in event_type or "validation" in event_type:
            return self._YELLOW
        if event_type.endswith("completed") or event_type.endswith("validated") or event_type.endswith("success"):
            return self._GREEN
        if "provider" in event_type:
            return self._BLUE
        return self._CYAN

    def _paint(self, text: str, *codes: str) -> str:
        if not self.use_color:
            return text
        joined = "".join(code for code in codes if code)
        return f"{joined}{text}{self._RESET}" if joined else text
