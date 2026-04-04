from __future__ import annotations

import asyncio
import json
from pathlib import Path

from PIL import Image

import dslighting.benchmark.grading.llm_judge as llm_judge_module
from dslighting.benchmark.grading.llm_judge import (
    ENV_JUDGE_IMAGE_MODEL,
    ENV_JUDGE_MODEL,
    judge_image,
    text_score,
    vlm_score,
)
from dslighting.debug.api import get_debug_session, init_debug


class _Usage:
    prompt_tokens = 11
    completion_tokens = 7
    total_tokens = 18


class _Message:
    def __init__(self, content: str) -> None:
        self.role = "assistant"
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _Response:
    def __init__(self, content: str) -> None:
        self.choices = [_Choice(content)]
        self.usage = _Usage()

    def model_dump(self) -> dict:
        return {
            "choices": [{"message": {"role": "assistant", "content": self.choices[0].message.content}}],
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
            },
        }


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _close_session() -> None:
    session = get_debug_session()
    if session is not None:
        asyncio.run(session.close())


def _reset_image_judge_capabilities() -> None:
    llm_judge_module._JSON_MODE_UNSUPPORTED_CAPABILITIES.clear()


def test_text_judge_emits_completed_and_preserves_max_tokens(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps({"judge-text-model": {"api_key": "secret", "api_base": "https://example.com/v1"}}),
    )
    monkeypatch.setenv(ENV_JUDGE_MODEL, "judge-text-model")

    captured: list[dict] = []

    def _fake_completion(**kwargs):
        captured.append(kwargs)
        return _Response('{"score": 77, "reason": "looks correct"}')

    monkeypatch.setattr("litellm.completion", _fake_completion)

    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)
    try:
        score = text_score("predicted", "gold")
        assert score == 77.0
    finally:
        _close_session()

    assert captured and captured[0]["max_tokens"] == 128
    assert session.output_dir is not None

    events = _load_jsonl(session.output_dir / "events.jsonl")
    event_types = [entry["event_type"] for entry in events]
    assert "llm.call.started" in event_types
    assert "llm.request.prepared" in event_types
    assert "llm.response.received" in event_types
    assert "llm.response.validated" in event_types
    assert "llm.call.completed" in event_types


def test_image_judge_sanitizes_base64_and_emits_validation_failure(monkeypatch, tmp_path: Path) -> None:
    _reset_image_judge_capabilities()
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps({"judge-image-model": {"api_key": "secret", "api_base": "https://example.com/v1"}}),
    )
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    captured: list[dict] = []

    def _fake_completion(**kwargs):
        captured.append(kwargs)
        return _Response("not valid json")

    monkeypatch.setattr("litellm.completion", _fake_completion)

    pred = Image.new("RGB", (6, 6), color="red")
    gold = Image.new("RGB", (6, 6), color="blue")

    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)
    try:
        score = vlm_score(pred, gold)
        assert score is None
    finally:
        _close_session()

    assert captured and captured[0]["max_tokens"] == 256
    assert captured[0]["response_format"] == {"type": "json_object"}
    assert session.output_dir is not None

    events = _load_jsonl(session.output_dir / "events.jsonl")
    payloads = _load_jsonl(session.output_dir / "payloads.jsonl")
    event_types = [entry["event_type"] for entry in events]
    assert "llm.call.started" in event_types
    assert "llm.request.prepared" in event_types
    assert "llm.response.received" in event_types
    assert "llm.validation.failed" in event_types
    assert "llm.call.failed" in event_types
    assert "llm.call.completed" not in event_types

    request_payload = next(entry for entry in payloads if entry["kind"] == "request_messages")
    payload_json = json.dumps(request_payload["body"], ensure_ascii=False)
    assert "inline_base64_image" in payload_json
    assert "<redacted>" in payload_json
    assert "data:image/png;base64,iVBOR" not in payload_json


def test_image_judge_averages_three_valid_samples(monkeypatch, tmp_path: Path) -> None:
    _reset_image_judge_capabilities()
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps({"judge-image-model": {"api_key": "secret", "api_base": "https://example.com/v1"}}),
    )
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    responses = [
        _Response(
            json.dumps(
                {
                    "analysis": {key: "ok" for key in ("chart_type", "axes_semantics", "pattern_fidelity", "style_legend")},
                    "subscores": {
                        "chart_type": 20,
                        "axes_semantics": 18,
                        "pattern_fidelity": 19,
                        "style_legend": 17,
                    },
                    "score": 74,
                    "confidence": 0.8,
                    "reason": "close match",
                }
            )
        ),
        _Response(
            json.dumps(
                {
                    "analysis": {key: "ok" for key in ("chart_type", "axes_semantics", "pattern_fidelity", "style_legend")},
                    "subscores": {
                        "chart_type": 22,
                        "axes_semantics": 20,
                        "pattern_fidelity": 20,
                        "style_legend": 18,
                    },
                    "score": 80,
                    "confidence": 0.7,
                    "reason": "strong match",
                }
            )
        ),
        _Response(
            json.dumps(
                {
                    "analysis": {key: "ok" for key in ("chart_type", "axes_semantics", "pattern_fidelity", "style_legend")},
                    "subscores": {
                        "chart_type": 21,
                        "axes_semantics": 19,
                        "pattern_fidelity": 19,
                        "style_legend": 17,
                    },
                    "score": 76,
                    "confidence": 0.75,
                    "reason": "good match",
                }
            )
        ),
    ]
    captured: list[dict] = []

    def _fake_completion(**kwargs):
        captured.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr("litellm.completion", _fake_completion)

    pred = Image.new("RGB", (6, 6), color="red")
    gold = Image.new("RGB", (6, 6), color="blue")

    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)
    try:
        result = judge_image(pred, gold, threshold=70.0)
        assert result == 1.0
    finally:
        _close_session()

    assert len(captured) == 3
    events = _load_jsonl(session.output_dir / "events.jsonl")
    aggregate = next(entry for entry in events if entry["event_type"] == "judge.image.aggregate.completed")
    assert aggregate["metrics"]["samples_total"] == 3
    assert aggregate["metrics"]["samples_valid"] == 3
    assert round(float(aggregate["metrics"]["final_score"]), 2) == 76.67
    assert aggregate["tags"]["source"] == "vlm_mean"


def test_image_judge_falls_back_to_pixel_when_insufficient_valid_samples(monkeypatch, tmp_path: Path) -> None:
    _reset_image_judge_capabilities()
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps({"judge-image-model": {"api_key": "secret", "api_base": "https://example.com/v1"}}),
    )
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    responses = [
        _Response(
            json.dumps(
                {
                    "analysis": {key: "ok" for key in ("chart_type", "axes_semantics", "pattern_fidelity", "style_legend")},
                    "subscores": {
                        "chart_type": 3,
                        "axes_semantics": 2,
                        "pattern_fidelity": 3,
                        "style_legend": 2,
                    },
                    "score": 10,
                    "confidence": 0.4,
                    "reason": "poor match",
                }
            )
        ),
        _Response("not valid json"),
        _Response("also not valid json"),
    ]

    def _fake_completion(**kwargs):
        return responses.pop(0)

    monkeypatch.setattr("litellm.completion", _fake_completion)

    pred = Image.new("RGB", (6, 6), color="red")
    gold = Image.new("RGB", (6, 6), color="red")

    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)
    try:
        result = judge_image(pred, gold, threshold=70.0)
        assert result == 1.0
    finally:
        _close_session()

    events = _load_jsonl(session.output_dir / "events.jsonl")
    aggregate = next(entry for entry in events if entry["event_type"] == "judge.image.aggregate.completed")
    assert aggregate["metrics"]["samples_total"] == 3
    assert aggregate["metrics"]["samples_valid"] == 1
    assert aggregate["tags"]["source"] == "pixel_fallback"


def test_image_judge_retries_without_response_format_when_json_mode_is_unsupported(monkeypatch, tmp_path: Path) -> None:
    _reset_image_judge_capabilities()
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps({"judge-image-model": {"api_key": "secret", "api_base": "https://example.com/v1"}}),
    )
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    captured: list[dict] = []

    def _structured_response(score: int) -> _Response:
        return _Response(
            json.dumps(
                {
                    "analysis": {key: "ok" for key in ("chart_type", "axes_semantics", "pattern_fidelity", "style_legend")},
                    "subscores": {
                        "chart_type": score // 4,
                        "axes_semantics": score // 4,
                        "pattern_fidelity": score // 4,
                        "style_legend": score - 3 * (score // 4),
                    },
                    "score": score,
                    "confidence": 0.8,
                    "reason": "good match",
                }
            )
        )

    prompt_only_responses = [_structured_response(84), _structured_response(82), _structured_response(80)]

    def _fake_completion(**kwargs):
        captured.append(kwargs)
        if kwargs.get("response_format") is not None:
            raise RuntimeError("litellm.BadRequestError: OpenAIException - Json mode is not supported for this model.")
        return prompt_only_responses.pop(0)

    monkeypatch.setattr("litellm.completion", _fake_completion)

    pred = Image.new("RGB", (6, 6), color="red")
    gold = Image.new("RGB", (6, 6), color="blue")

    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)
    try:
        result = judge_image(pred, gold, threshold=70.0)
        assert result == 1.0
    finally:
        _close_session()

    assert len(captured) == 4
    assert captured[0]["response_format"] == {"type": "json_object"}
    assert all("response_format" not in kwargs for kwargs in captured[1:])

    events = _load_jsonl(session.output_dir / "events.jsonl")
    aggregate = next(entry for entry in events if entry["event_type"] == "judge.image.aggregate.completed")
    assert aggregate["metrics"]["samples_total"] == 3
    assert aggregate["metrics"]["samples_valid"] == 3
    assert aggregate["tags"]["source"] == "vlm_mean"

    completed_events = [entry for entry in events if entry["event_type"] == "llm.call.completed"]
    assert completed_events
    assert all(entry["tags"]["judge_request_mode"] == "prompt_enforced_json" for entry in completed_events)


def test_image_judge_stops_early_after_prompt_only_provider_failure(monkeypatch, tmp_path: Path) -> None:
    _reset_image_judge_capabilities()
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps({"judge-image-model": {"api_key": "secret", "api_base": "https://example.com/v1"}}),
    )
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    captured: list[dict] = []

    def _fake_completion(**kwargs):
        captured.append(kwargs)
        if kwargs.get("response_format") is not None:
            raise RuntimeError("litellm.BadRequestError: OpenAIException - Json mode is not supported for this model.")
        raise RuntimeError("litellm.InternalServerError: OpenAIException - Request processing failed due to an unknown error.")

    monkeypatch.setattr("litellm.completion", _fake_completion)

    pred = Image.new("RGB", (1800, 1200), color="red")
    gold = Image.new("RGB", (900, 900), color="blue")

    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)
    try:
        result = judge_image(pred, gold, threshold=70.0)
        assert result == 0.0
    finally:
        _close_session()

    assert len(captured) == 2
    assert captured[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in captured[1]

    events = _load_jsonl(session.output_dir / "events.jsonl")
    aggregate = next(entry for entry in events if entry["event_type"] == "judge.image.aggregate.completed")
    assert aggregate["metrics"]["samples_total"] == 1
    assert aggregate["metrics"]["samples_planned"] == 3
    assert aggregate["metrics"]["samples_valid"] == 0
    assert aggregate["tags"]["source"] == "pixel_fallback"
    assert aggregate["tags"]["stopped_early"] is True
    assert aggregate["tags"]["stop_reason"] == "provider_transport_error"


def test_image_judge_stops_early_when_threshold_is_unreachable(monkeypatch, tmp_path: Path) -> None:
    _reset_image_judge_capabilities()
    monkeypatch.setenv(
        "LLM_MODEL_CONFIGS",
        json.dumps({"judge-image-model": {"api_key": "secret", "api_base": "https://example.com/v1"}}),
    )
    monkeypatch.setenv(ENV_JUDGE_IMAGE_MODEL, "judge-image-model")

    captured: list[dict] = []

    def _structured_response(score: int) -> _Response:
        return _Response(
            json.dumps(
                {
                    "analysis": {key: "ok" for key in ("chart_type", "axes_semantics", "pattern_fidelity", "style_legend")},
                    "subscores": {
                        "chart_type": score // 4,
                        "axes_semantics": score // 4,
                        "pattern_fidelity": score // 4,
                        "style_legend": score - 3 * (score // 4),
                    },
                    "score": score,
                    "confidence": 0.6,
                    "reason": "match quality",
                }
            )
        )

    responses = [_structured_response(40), _structured_response(35), _structured_response(100)]

    def _fake_completion(**kwargs):
        captured.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr("litellm.completion", _fake_completion)

    pred = Image.new("RGB", (6, 6), color="red")
    gold = Image.new("RGB", (6, 6), color="blue")

    session = init_debug(enabled=True, profile="full", output_dir=str(tmp_path), console_output=False)
    try:
        result = judge_image(pred, gold, threshold=60.0)
        assert result == 0.0
    finally:
        _close_session()

    assert len(captured) == 2
    events = _load_jsonl(session.output_dir / "events.jsonl")
    aggregate = next(entry for entry in events if entry["event_type"] == "judge.image.aggregate.completed")
    assert aggregate["metrics"]["samples_total"] == 2
    assert aggregate["metrics"]["samples_planned"] == 3
    assert aggregate["metrics"]["samples_valid"] == 2
    assert aggregate["tags"]["source"] == "vlm_mean"
    assert aggregate["tags"]["stopped_early"] is True
    assert aggregate["tags"]["stop_reason"] == "threshold_unreachable"
