from __future__ import annotations

import json
from pathlib import Path

from dslighting.debug.sft_export import export_llm_calls_to_sft


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def test_export_llm_calls_to_sft_writes_strict_and_full_datasets(tmp_path: Path) -> None:
    llm_calls_path = tmp_path / "llm_calls.jsonl"
    _write_jsonl(
        llm_calls_path,
        [
            {
                "call_id": "call-1",
                "model": "openai/test-model",
                "provider": "openai",
                "timestamp_utc": "2026-04-04T10:00:00Z",
                "duration_seconds": 1.23,
                "response_format": "text",
                "messages": [
                    {"role": "system", "content": "Be terse."},
                    {"role": "user", "content": "Say hello."},
                ],
                "response": "Hello.",
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
                "cost": 0.01,
                "cost_per_token": 0.0008,
            }
        ],
    )

    summary = export_llm_calls_to_sft(
        llm_calls_path=llm_calls_path,
        export_dir=tmp_path / "exports",
        task_id="dabench-0-mean-fare-paid",
        workflow="aide",
        benchmark="dabench",
        run_name="run_123",
        workspace_dir="/tmp/workspace",
        export_stem="react_dabench_task0",
    )

    assert summary["record_count"] == 1

    sft_jsonl_path = Path(summary["paths"]["sft_jsonl"])
    full_json_path = Path(summary["paths"]["full_json"])

    sft_lines = sft_jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(sft_lines) == 1
    strict_record = json.loads(sft_lines[0])
    assert strict_record == {
        "messages": [
            {"role": "system", "content": "Be terse."},
            {"role": "user", "content": "Say hello."},
            {"role": "assistant", "content": "Hello."},
        ]
    }

    full_payload = json.loads(full_json_path.read_text(encoding="utf-8"))
    assert full_payload["task_id"] == "dabench-0-mean-fare-paid"
    assert full_payload["record_count"] == 1
    assert full_payload["records"][0]["response"] == {
        "role": "assistant",
        "content": "Hello.",
    }
    assert full_payload["records"][0]["response_normalized"] == {
        "role": "assistant",
        "content": "Hello.",
    }
    assert full_payload["records"][0]["response_repaired"] is False
    assert full_payload["records"][0]["messages"][-1] == {
        "role": "assistant",
        "content": "Hello.",
    }


def test_export_llm_calls_to_sft_repairs_unclosed_answer_for_react(tmp_path: Path) -> None:
    llm_calls_path = tmp_path / "llm_calls.jsonl"
    _write_jsonl(
        llm_calls_path,
        [
            {
                "call_id": "call-1",
                "model": "openai/test-model",
                "provider": "openai",
                "timestamp_utc": "2026-04-04T10:00:00Z",
                "duration_seconds": 1.23,
                "response_format": "text",
                "messages": [
                    {"role": "system", "content": "Be terse."},
                    {"role": "user", "content": "Finish the task."},
                ],
                "response": "<Think>Done.</Think>\n<Answer>42",
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
            }
        ],
    )

    summary = export_llm_calls_to_sft(
        llm_calls_path=llm_calls_path,
        export_dir=tmp_path / "exports",
        task_id="dacode-di-csv-031",
        workflow="react",
        benchmark="dacode",
    )

    sft_json_path = Path(summary["paths"]["sft_json"])
    full_json_path = Path(summary["paths"]["full_json"])

    sft_payload = json.loads(sft_json_path.read_text(encoding="utf-8"))
    assert sft_payload["record_count"] == 1
    assert sft_payload["records"][0]["messages"][-1] == {
        "role": "assistant",
        "content": "<Think>Done.</Think>\n<Answer>42\n</Answer>",
    }

    full_payload = json.loads(full_json_path.read_text(encoding="utf-8"))
    record = full_payload["records"][0]
    assert record["response"]["content"] == "<Think>Done.</Think>\n<Answer>42"
    assert record["response_normalized"]["content"] == "<Think>Done.</Think>\n<Answer>42\n</Answer>"
    assert record["response_repaired"] is True
    assert record["repair_reason"] == "added missing </Answer> closing tag"


def test_export_llm_calls_to_sft_skips_legacy_final_answer_from_react_sft(tmp_path: Path) -> None:
    llm_calls_path = tmp_path / "llm_calls.jsonl"
    _write_jsonl(
        llm_calls_path,
        [
            {
                "call_id": "call-1",
                "model": "openai/test-model",
                "provider": "openai",
                "timestamp_utc": "2026-04-04T10:00:00Z",
                "duration_seconds": 1.23,
                "response_format": "text",
                "messages": [
                    {"role": "system", "content": "Be terse."},
                    {"role": "user", "content": "Finish the task."},
                ],
                "response": "<Think>Done.</Think>\n<Final Answer>42</Final Answer>",
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
            }
        ],
    )

    summary = export_llm_calls_to_sft(
        llm_calls_path=llm_calls_path,
        export_dir=tmp_path / "exports",
        task_id="dacode-di-csv-031",
        workflow="react",
        benchmark="dacode",
    )

    sft_json_path = Path(summary["paths"]["sft_json"])
    full_json_path = Path(summary["paths"]["full_json"])

    sft_payload = json.loads(sft_json_path.read_text(encoding="utf-8"))
    assert sft_payload["record_count"] == 0

    full_payload = json.loads(full_json_path.read_text(encoding="utf-8"))
    record = full_payload["records"][0]
    assert record["response"]["content"] == "<Think>Done.</Think>\n<Final Answer>42</Final Answer>"
    assert record["response_repaired"] is False
    assert record["sft_eligible"] is False
