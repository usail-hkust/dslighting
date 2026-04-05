"""Export LLM call telemetry into chat-SFT friendly JSON and JSONL files."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dslighting.workflows.search.react.protocol import (
    extract_answer_block,
    normalize_react_reply,
    validate_turn_structure,
)


def export_llm_calls_to_sft(
    *,
    llm_calls_path: Path,
    export_dir: Path,
    task_id: str,
    workflow: str,
    benchmark: str,
    run_name: str | None = None,
    workspace_dir: str | None = None,
    export_stem: str | None = None,
    session_messages_path: Path | None = None,
) -> dict[str, Any]:
    """Export raw llm_calls telemetry into strict SFT and full debug datasets."""
    llm_calls = _read_jsonl(llm_calls_path)
    export_dir.mkdir(parents=True, exist_ok=True)

    stem = export_stem or f"{workflow}_{benchmark}_{_slugify(task_id)}"
    created_at_utc = datetime.now(timezone.utc).isoformat()

    full_records = [
        _build_full_record(
            call=call,
            index=index,
            task_id=task_id,
            workflow=workflow,
            benchmark=benchmark,
            run_name=run_name,
            workspace_dir=workspace_dir,
            llm_calls_path=llm_calls_path,
        )
        for index, call in enumerate(llm_calls, start=1)
    ]
    sft_records = [
        {"messages": record["messages"]}
        for record in full_records
        if record["sft_eligible"]
    ]
    session_records = _build_session_sft_records(
        full_records=full_records,
        workflow=workflow,
        workspace_dir=workspace_dir,
        session_messages_path=session_messages_path,
    )

    full_bundle = {
        "created_at_utc": created_at_utc,
        "task_id": task_id,
        "workflow": workflow,
        "benchmark": benchmark,
        "run_name": run_name,
        "workspace_dir": workspace_dir,
        "source_llm_calls_path": str(llm_calls_path),
        "record_count": len(full_records),
        "records": full_records,
    }
    sft_bundle = {
        "created_at_utc": created_at_utc,
        "task_id": task_id,
        "workflow": workflow,
        "benchmark": benchmark,
        "run_name": run_name,
        "record_count": len(sft_records),
        "records": sft_records,
    }
    session_bundle = {
        "created_at_utc": created_at_utc,
        "task_id": task_id,
        "workflow": workflow,
        "benchmark": benchmark,
        "run_name": run_name,
        "record_count": len(session_records),
        "records": session_records,
    }

    full_json_path = export_dir / f"{stem}_llm_full.json"
    full_jsonl_path = export_dir / f"{stem}_llm_full.jsonl"
    sft_json_path = export_dir / f"{stem}_sft.json"
    sft_jsonl_path = export_dir / f"{stem}_sft.jsonl"
    session_json_path = export_dir / f"{stem}_session_sft.json"
    session_jsonl_path = export_dir / f"{stem}_session_sft.jsonl"

    _write_json(full_json_path, full_bundle)
    _write_jsonl(full_jsonl_path, full_records)
    _write_json(sft_json_path, sft_bundle)
    _write_jsonl(sft_jsonl_path, sft_records)
    _write_json(session_json_path, session_bundle)
    _write_jsonl(session_jsonl_path, session_records)

    return {
        "task_id": task_id,
        "record_count": len(full_records),
        "session_record_count": len(session_records),
        "full_records": full_records,
        "sft_records": sft_records,
        "session_records": session_records,
        "paths": {
            "source_llm_calls": str(llm_calls_path),
            "full_json": str(full_json_path),
            "full_jsonl": str(full_jsonl_path),
            "sft_json": str(sft_json_path),
            "sft_jsonl": str(sft_jsonl_path),
            "session_json": str(session_json_path),
            "session_jsonl": str(session_jsonl_path),
        },
    }


def _build_full_record(
    *,
    call: dict[str, Any],
    index: int,
    task_id: str,
    workflow: str,
    benchmark: str,
    run_name: str | None,
    workspace_dir: str | None,
    llm_calls_path: Path,
) -> dict[str, Any]:
    input_messages_raw = copy.deepcopy(call.get("messages") or [])
    input_messages = _normalize_messages_for_sft(
        input_messages_raw,
        workflow=workflow,
    )
    raw_response_content = _normalize_content(call.get("response"))
    normalized_response_content, repaired, repair_reason = _normalize_assistant_response(
        raw_response_content,
        workflow=workflow,
    )
    assistant_message_raw = {
        "role": "assistant",
        "content": raw_response_content,
    }
    assistant_message = {
        "role": "assistant",
        "content": normalized_response_content,
    }
    messages = input_messages + [assistant_message]
    return {
        "id": str(call.get("call_id") or f"{task_id}:{index}"),
        "call_index": index,
        "task_id": task_id,
        "workflow": workflow,
        "benchmark": benchmark,
        "run_name": run_name,
        "workspace_dir": workspace_dir,
        "source_llm_calls_path": str(llm_calls_path),
        "timestamp_utc": call.get("timestamp_utc"),
        "model": call.get("model"),
        "provider": call.get("provider"),
        "response_format": call.get("response_format"),
        "duration_seconds": call.get("duration_seconds"),
        "input_messages": input_messages,
        "input_messages_raw": input_messages_raw,
        "response": assistant_message_raw,
        "response_normalized": assistant_message,
        "response_repaired": repaired,
        "repair_reason": repair_reason,
        "messages": messages,
        "messages_raw": input_messages_raw + [assistant_message_raw],
        "sft_eligible": _messages_are_sft_eligible(messages, workflow=workflow),
        "usage": copy.deepcopy(call.get("usage")),
        "cost": call.get("cost"),
        "cost_per_token": call.get("cost_per_token"),
    }


def _build_session_sft_records(
    *,
    full_records: list[dict[str, Any]],
    workflow: str,
    workspace_dir: str | None,
    session_messages_path: Path | None,
) -> list[dict[str, Any]]:
    messages = _resolve_session_messages(
        full_records=full_records,
        workflow=workflow,
        workspace_dir=workspace_dir,
        session_messages_path=session_messages_path,
    )
    if not messages:
        return []
    if not _session_messages_are_sft_eligible(messages, workflow=workflow):
        return []
    return [{"messages": messages}]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _normalize_content(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_normalize_content(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_content(item) for key, item in value.items()}
    return str(value)


def _normalize_messages_for_sft(
    messages: list[dict[str, Any]],
    *,
    workflow: str,
) -> list[dict[str, Any]]:
    normalized_messages: list[dict[str, Any]] = []
    for message in messages:
        normalized = copy.deepcopy(message)
        content = normalized.get("content")
        if workflow == "react" and normalized.get("role") == "assistant" and isinstance(content, str):
            normalized["content"] = normalize_react_reply(content).normalized_content
        normalized_messages.append(normalized)
    return normalized_messages


def _resolve_session_messages(
    *,
    full_records: list[dict[str, Any]],
    workflow: str,
    workspace_dir: str | None,
    session_messages_path: Path | None,
) -> list[dict[str, Any]]:
    if workflow == "react":
        path = session_messages_path
        if path is None and workspace_dir:
            path = Path(workspace_dir) / "artifacts" / "messages.json"
        if path is not None:
            payload = _read_json(path)
            if isinstance(payload, list):
                return _normalize_messages_for_sft(payload, workflow=workflow)

    if not full_records:
        return []
    return copy.deepcopy(full_records[-1]["messages"])


def _normalize_assistant_response(
    content: Any,
    *,
    workflow: str,
) -> tuple[Any, bool, str | None]:
    normalized_content = _normalize_content(content)
    if workflow != "react" or not isinstance(normalized_content, str):
        return normalized_content, False, None
    normalized = normalize_react_reply(normalized_content)
    return normalized.normalized_content, normalized.repaired, normalized.repair_reason


def _messages_are_sft_eligible(
    messages: list[dict[str, Any]],
    *,
    workflow: str,
) -> bool:
    if workflow != "react":
        return True
    for message in messages:
        if message.get("role") != "assistant":
            continue
        content = message.get("content")
        if not isinstance(content, str):
            return False
        is_valid, _ = validate_turn_structure(content)
        if not is_valid:
            return False
    return True


def _session_messages_are_sft_eligible(
    messages: list[dict[str, Any]],
    *,
    workflow: str,
) -> bool:
    if not messages:
        return False
    if not _messages_are_sft_eligible(messages, workflow=workflow):
        return False
    if workflow != "react":
        return True

    last_message = messages[-1]
    if last_message.get("role") != "assistant":
        return False

    content = last_message.get("content")
    if not isinstance(content, str):
        return False

    return extract_answer_block(content) is not None


def _slugify(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
