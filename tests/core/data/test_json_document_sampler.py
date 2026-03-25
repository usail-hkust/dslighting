from __future__ import annotations

from dslighting.core.data.introspection.samplers.document import DocumentSampler


def test_document_sampler_handles_standard_json() -> None:
    sampler = DocumentSampler(preview_lines=3)
    summary = sampler._summarize_json_document('{"a": 1, "b": 2}', suffix=".json")
    assert summary[0] == "Kind: json document"
    assert "Top-level keys" in summary[1]


def test_document_sampler_handles_pretty_printed_json() -> None:
    sampler = DocumentSampler(preview_lines=3)
    text = '{\n  "a": 1,\n  "b": 2\n}\n'
    summary = sampler._summarize_json_document(text, suffix=".json")
    assert summary[0] == "Kind: json document"
    assert "Top-level keys" in summary[1]


def test_document_sampler_handles_jsonl() -> None:
    sampler = DocumentSampler(preview_lines=3)
    text = '{"id": 1, "value": "a"}\n{"id": 2, "value": "b"}\n'
    summary = sampler._summarize_json_document(text, suffix=".jsonl")
    assert summary[0] == "Kind: jsonl document"
    assert "Records: 2" in summary
    assert any("Record keys" in line for line in summary)


def test_document_sampler_handles_jsonl_with_blank_lines() -> None:
    sampler = DocumentSampler(preview_lines=4)
    text = '\n{"id": 1}\n\n{"id": 2}\n'
    summary = sampler._summarize_json_document(text, suffix=".jsonl")
    assert summary[0] == "Kind: jsonl document"
    assert "Records: 2" in summary


def test_document_sampler_handles_jsonl_with_partial_bad_lines() -> None:
    sampler = DocumentSampler(preview_lines=4)
    text = '{"id": 1}\nnot-json\n{"id": 2}\n'
    summary = sampler._summarize_json_document(text, suffix=".jsonl")
    assert summary[0] == "Kind: jsonl document"
    assert "Records: 2" in summary
    assert "Failed lines: 1" in summary


def test_document_sampler_degrades_bad_json_to_json_like() -> None:
    sampler = DocumentSampler(preview_lines=3)
    text = '{"a": 1\n{"b": 2}'
    summary = sampler._summarize_json_document(text, suffix=".json")
    assert summary[0] == "Kind: json-like document"
    assert "Parse Status: failed" in summary
