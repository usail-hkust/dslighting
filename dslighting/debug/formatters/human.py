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
                    lines.extend(self._render_payload(
                        label=label,
                        payload=payload,
                        payload_ref=payload_ref,
                        payload_store=payload_store,
                    ))

        return "\n".join(lines)

    def format_generic_event(
        self,
        event,
        payload_store,
        *,
        printed_payload_refs: set[str] | None = None,
    ) -> str:
        if printed_payload_refs is None:
            printed_payload_refs = set()
        run = event.run
        node = event.node
        kind = self._event_kind_label(event.event_type)
        lines = [
            self._paint(f"[{kind}]", self._CYAN, self._BOLD),
            "  "
            + " ".join(
                [
                    f"run={getattr(run, 'run_id', 'N/A')}",
                    f"task={getattr(run, 'task_id', 'N/A') or 'N/A'}",
                    f"workflow={getattr(run, 'workflow_name', 'N/A') or 'N/A'}",
                    f"node={getattr(node, 'node_id', 'N/A') or 'N/A'}",
                ]
            ),
            f"- {self._paint(event.event_type, self._event_color(event.event_type), self._BOLD)}: {event.summary}",
        ]
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
                lines.extend(self._render_payload(
                    label=label,
                    payload=payload,
                    payload_ref=payload_ref,
                    payload_store=payload_store,
                ))
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
        max_tokens = tags.pop("max_tokens", None)

        if provider is not None:
            lines.append(f"  Provider: {provider}")
        if api_base is not None:
            lines.append(f"  API Base: {api_base}")
        if temperature is not None:
            lines.append(f"  Temperature: {temperature}")
        if max_tokens is not None:
            lines.append(f"  Max Tokens: {max_tokens}")
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

    def _render_payload(
        self,
        *,
        label: str,
        payload: Any,
        payload_ref=None,
        payload_store=None,
    ) -> list[str]:
        if label == "request_messages" and isinstance(payload, list):
            section_map = self._resolve_section_map(payload_ref, payload_store)
            return self._render_request_messages(payload, section_map=section_map)
        if label.endswith("response_body") and isinstance(payload, dict):
            return self._render_response_payload(payload)
        return self._indent_lines(self._stringify(payload), prefix="    ")

    def _resolve_section_map(self, payload_ref: Any, payload_store: Any) -> list | None:
        """Retrieve the section_map associated with a request_messages payload ref."""
        if payload_ref is None or payload_store is None:
            return None
        section_map_ref = getattr(payload_ref, "section_map_ref", None)
        if not section_map_ref:
            return None
        try:
            return payload_store.get(section_map_ref)
        except Exception:
            return None

    def _render_request_messages(
        self,
        messages: list,
        *,
        section_map: list | None,
    ) -> list[str]:
        lines: list[str] = []
        for idx, item in enumerate(messages, start=1):
            role = "unknown"
            content = item
            if isinstance(item, dict):
                role = str(item.get("role", "unknown"))
                content = item.get("content", "")
            lines.append(f"    [{idx}] {role}:")
            lines.extend(self._render_request_content_with_map(content, section_map=section_map))
        return lines

    def _render_request_content_with_map(
        self,
        content: Any,
        *,
        section_map: list | None,
    ) -> list[str]:
        """Render the exact sanitized request content sent to the LLM.

        request_messages must be lossless in console output. Other payload types can
        still use max_inline_chars, but LLM request rendering should not fold sections
        or append a preview-only "[truncated]" marker because that makes the console
        disagree with the stored payload and the provider request body.
        """
        _ = section_map
        if not isinstance(content, list):
            return self._indent_lines(self._stringify_full(content), prefix="      ")

        lines: list[str] = []
        image_idx = 0
        for item in content:
            if not isinstance(item, dict):
                lines.extend(self._indent_lines(self._stringify_full(item), prefix="      "))
                continue

            item_type = item.get("type")
            if item_type == "text":
                text = str(item.get("text", ""))
                lines.extend(self._indent_lines(text, prefix="      "))
                continue

            if item_type == "image_url":
                image_idx += 1
                image_url = item.get("image_url", {})
                if isinstance(image_url, dict) and image_url.get("kind") == "inline_base64_image":
                    mime_type = image_url.get("mime_type", "unknown")
                    approx_chars = image_url.get("approx_chars", 0)
                    lines.append(
                        f"      [image {image_idx}] inline_base64_image mime={mime_type} chars={approx_chars}"
                    )
                    continue

            lines.extend(self._indent_lines(self._stringify_full(item), prefix="      "))
        return lines or self._indent_lines(self._stringify_full(content), prefix="      ")

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

    def _render_request_content(self, content: Any) -> list[str]:
        """Legacy path used for non-request_messages payloads."""
        if not isinstance(content, list):
            return self._indent_lines(self._stringify(content), prefix="      ")

        lines: list[str] = []
        image_idx = 0
        for item in content:
            if not isinstance(item, dict):
                lines.extend(self._indent_lines(self._stringify(item), prefix="      "))
                continue

            item_type = item.get("type")
            if item_type == "text":
                lines.extend(self._indent_lines(str(item.get("text", "")), prefix="      "))
                continue

            if item_type == "image_url":
                image_idx += 1
                image_url = item.get("image_url", {})
                if isinstance(image_url, dict) and image_url.get("kind") == "inline_base64_image":
                    mime_type = image_url.get("mime_type", "unknown")
                    approx_chars = image_url.get("approx_chars", 0)
                    lines.append(
                        f"      [image {image_idx}] inline_base64_image mime={mime_type} chars={approx_chars}"
                    )
                    continue

            lines.extend(self._indent_lines(self._stringify(item), prefix="      "))
        return lines or self._indent_lines(self._stringify(content), prefix="      ")

    # ------------------------------------------------------------------
    # Section-map-aware structured preview
    # ------------------------------------------------------------------

    _CRITICAL_SECTION_NAMES = frozenset({
        "Submission Artifact Requirements",
        "Submission Format Requirements",
        "CRITICAL I/O REQUIREMENTS",
    })
    _FOLDABLE_SECTION_NAMES = frozenset({"Data Schema Analysis"})
    # Fallback header patterns for when section_map is unavailable
    _FALLBACK_CRITICAL_HEADERS = (
        "## Submission Artifact Requirements",
        "## Submission Format Requirements",
        "--- CRITICAL I/O REQUIREMENTS ---",
    )

    def _render_text_with_section_map(self, text: str, section_map: list) -> list[str]:
        """Render text using section_map spans: preserve critical, fold Data Schema Analysis."""
        if len(text) <= self.max_inline_chars:
            return self._indent_lines(text, prefix="      ")

        lines: list[str] = []
        total_chars = len(text)
        prev_end = 0
        folded_count = 0
        folded_chars = 0

        for span in section_map:
            name = span.get("name") if isinstance(span, dict) else getattr(span, "name", "")
            start = span.get("start") if isinstance(span, dict) else getattr(span, "start", 0)
            end = span.get("end") if isinstance(span, dict) else getattr(span, "end", 0)
            critical = span.get("critical") if isinstance(span, dict) else getattr(span, "critical", False)
            foldable = span.get("foldable") if isinstance(span, dict) else getattr(span, "foldable", False)

            # Render any gap between spans
            if prev_end < start:
                gap = text[prev_end:start]
                if gap.strip():
                    lines.extend(self._indent_lines(gap, prefix="      "))

            section_text = text[start:end]
            if critical or not foldable:
                lines.extend(self._indent_lines(section_text, prefix="      "))
            else:
                # Fold: show first line only + summary
                first_line = section_text.split("\n", 1)[0]
                lines.append(f"      {first_line}")
                lines.append(f"      ... [folded section '{name}' / {len(section_text)} chars omitted for console preview]")
                folded_count += 1
                folded_chars += len(section_text)

            prev_end = end

        # Any trailing text after last span
        if prev_end < total_chars:
            trailing = text[prev_end:]
            if trailing.strip():
                lines.extend(self._indent_lines(trailing, prefix="      "))

        if folded_count:
            lines.append(
                f"      ... [total: {folded_count} section(s) folded / "
                f"{folded_chars} chars omitted for console preview]"
            )
        return lines

    def _render_text_fallback_structured(self, text: str) -> list[str]:
        """Fallback structured preview when section_map is unavailable.

        Preserves critical headers and surrounding text; truncates middle sections.
        Not a formal contract — section_map path is preferred.
        """
        if len(text) <= self.max_inline_chars:
            return self._indent_lines(text, prefix="      ")

        # Find critical header positions
        critical_ranges: list[tuple[int, int]] = []
        for header in self._FALLBACK_CRITICAL_HEADERS:
            pos = text.find(header)
            if pos == -1:
                continue
            # Keep from header to next ## header or end (up to 2000 chars)
            next_section = len(text)
            for h in ("## ", "--- "):
                idx = text.find(h, pos + len(header))
                if idx != -1 and idx < next_section:
                    next_section = idx
            critical_ranges.append((pos, min(next_section, pos + 2000)))

        if not critical_ranges:
            return self._indent_lines(
                text[:self.max_inline_chars] + "\n... [truncated — no section_map available]",
                prefix="      ",
            )

        # Show beginning + critical sections
        lines: list[str] = []
        lines.extend(self._indent_lines(text[:min(500, len(text))], prefix="      "))
        lines.append("      ... [middle sections omitted — no section_map available]")
        for start, end in sorted(set(critical_ranges)):
            lines.extend(self._indent_lines(text[start:end], prefix="      "))
        return lines

    def _stringify(self, value: Any) -> str:
        if isinstance(value, str):
            text = value
        else:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        if len(text) > self.max_inline_chars:
            return text[: self.max_inline_chars] + "\n... [truncated]"
        return text

    @staticmethod
    def _stringify_full(value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)

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

    @staticmethod
    def _event_kind_label(event_type: str) -> str:
        if event_type.startswith("tool."):
            return "TOOL"
        if event_type.startswith("sandbox."):
            return "SANDBOX"
        return "EVENT"

    def _paint(self, text: str, *codes: str) -> str:
        if not self.use_color:
            return text
        joined = "".join(code for code in codes if code)
        return f"{joined}{text}{self._RESET}" if joined else text
