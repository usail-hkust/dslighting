"""
LLM-as-judge utilities for benchmark grading.

Two judge types are supported:
- Image judge : uses a VLM (JUDGE_IMAGE_MODEL) to compare scientific plots.
- Text judge  : uses a text LLM (JUDGE_MODEL) to evaluate free-form text or code output.

Model configuration is resolved from environment variables:
    JUDGE_MODEL=<model_name>        # text judge
    JUDGE_IMAGE_MODEL=<model_name>  # image judge

The long-term image-judge protocol is structured JSON with rubric-based subscores.
Legacy `[FINAL SCORE]: <n>` parsing remains temporarily for ScienceBench migration, but
it is not the primary contract.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import io
import json
import logging
import os
import re
from typing import Any

import numpy as np
from PIL import Image

from dslighting.core.config.llm_resolution import load_model_override_map
from dslighting.logging.events import emit_runtime_event
from dslighting.services.llm.observed_call import (
    completion_with_observability,
    emit_llm_event_sync,
    extract_response_content,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment variable names
# ---------------------------------------------------------------------------
ENV_JUDGE_MODEL = "JUDGE_MODEL"
ENV_JUDGE_IMAGE_MODEL = "JUDGE_IMAGE_MODEL"

# Default models – overridable via env vars
DEFAULT_JUDGE_MODEL = "openai/deepseek-ai/DeepSeek-V3.1-Terminus"
DEFAULT_JUDGE_IMAGE_MODEL = "openai/Qwen/Qwen2.5-VL-72B-Instruct"

# ---------------------------------------------------------------------------
# Image-judge protocol defaults
# ---------------------------------------------------------------------------
IMAGE_SCORE_FIELDS = (
    "chart_type",
    "axes_semantics",
    "pattern_fidelity",
    "style_legend",
)
LEGACY_BOOLEAN_FIELDS = {
    "same_type": "chart_type",
    "correct_axes": "axes_semantics",
    "correct_pattern": "pattern_fidelity",
    "correct_style": "style_legend",
}
DEFAULT_IMAGE_JUDGE_SAMPLES = 3
DEFAULT_IMAGE_JUDGE_MIN_VALID_SAMPLES = 2
DEFAULT_IMAGE_JUDGE_MAX_TOKENS = 256
DEFAULT_IMAGE_JUDGE_TEMPERATURE = 0.2
LEGACY_FINAL_SCORE_RE = re.compile(r"\[FINAL SCORE\]\s*:\s*([0-9]{1,3}(?:\.\d+)?)", re.IGNORECASE)
PLAIN_SCORE_RE = re.compile(r"(?:^|\b)(?:final\s+score|score)\s*[:=]\s*([0-9]{1,3}(?:\.\d+)?)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Default prompts
# ---------------------------------------------------------------------------

DEFAULT_IMAGE_JUDGE_PROMPT = """\
You are an expert judge for scientific visualizations.

You will compare two images:
- The FIRST image is the predicted plot.
- The SECOND image is the gold reference.

Evaluate the predicted image on these dimensions:
1. chart_type: whether the visualization type matches the task
2. axes_semantics: whether variables, labels, and units match
3. pattern_fidelity: whether trends, distributions, and relative magnitudes match
4. style_legend: whether colors, legend semantics, and layout are sufficiently consistent

Scoring rules:
- Each subscore must be an integer from 0 to 25.
- The total score must equal the sum of the four subscores, from 0 to 100.
- Focus on scientific correctness rather than pixel identity.
- If the task allows randomness, semantically correct plots may still deserve high scores.

Return strictly one JSON object with this schema:
{
  "analysis": {
    "chart_type": "short sentence",
    "axes_semantics": "short sentence",
    "pattern_fidelity": "short sentence",
    "style_legend": "short sentence"
  },
  "subscores": {
    "chart_type": 0,
    "axes_semantics": 0,
    "pattern_fidelity": 0,
    "style_legend": 0
  },
  "score": 0,
  "confidence": 0.0,
  "reason": "one short summary sentence"
}

Do not output markdown. Do not output any extra text."""

DEFAULT_TEXT_JUDGE_SYSTEM = """\
You are an expert evaluator for data science and scientific tasks.
Score the predicted answer against the gold reference based on the provided criteria.
Output strictly a JSON object: {"score": <integer 0-100>, "reason": "<one sentence>"}
Nothing else."""

DEFAULT_TEXT_JUDGE_CRITERIA = "correctness, completeness, and accuracy"


@dataclass(frozen=True)
class JudgeImageSample:
    score: float
    confidence: float | None
    reason: str
    protocol: str
    normalized: dict[str, Any]
    duration_seconds: float
    usage: dict[str, Any]


@dataclass(frozen=True)
class JudgeImageAggregate:
    final_score: float
    sample_scores: tuple[float, ...]
    valid_samples: int
    total_samples: int
    source: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_model(env_var: str, default: str) -> str:
    return os.environ.get(env_var, "").strip() or default


def _get_litellm_kwargs(model: str) -> dict[str, Any]:
    """Build LiteLLM call kwargs by looking up the model in LLM_MODEL_CONFIGS."""
    config = load_model_override_map().get(model, {})
    kwargs: dict[str, Any] = {"model": model}

    api_keys = config.get("api_keys")
    api_key = config.get("api_key")
    if api_keys:
        kwargs["api_key"] = api_keys[0]
    elif api_key:
        kwargs["api_key"] = api_key

    if config.get("api_base"):
        kwargs["api_base"] = config["api_base"]
    if config.get("provider"):
        kwargs["custom_llm_provider"] = config["provider"]

    return kwargs


def _encode_pil(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _supports_response_format(model: str) -> bool:
    """
    Mirror `LLMService._supports_response_format()` for direct judge calls.

    Some models reject LiteLLM's `response_format` and require prompt-enforced JSON only.
    """
    raw_model = (model or "").strip()
    short_name = raw_model.split("/")[-1].strip().lower()
    if short_name.startswith("o4-mini-") or short_name == "o4-mini":
        return False
    if short_name == "kimi-k2-instruct-0905":
        return False
    return True


def _looks_like_legacy_prompt(prompt: str | None) -> bool:
    if not prompt:
        return False
    normalized = prompt.lower()
    return "[final score]" in normalized or "final score is preceded" in normalized


def _build_image_prompt(rubric_supplement: str | None = None) -> str:
    if not rubric_supplement or not rubric_supplement.strip():
        return DEFAULT_IMAGE_JUDGE_PROMPT
    return (
        DEFAULT_IMAGE_JUDGE_PROMPT
        + "\n\nTask-specific rubric supplement:\n"
        + rubric_supplement.strip()
    )


def _clip_score(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _coerce_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if not lines:
        return stripped
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    if lines and lines[0].strip().lower() == "json":
        lines = lines[1:]
    return "\n".join(lines).strip()


def _extract_first_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _parse_json_object_from_text(content: str) -> dict[str, Any]:
    candidates = [_strip_code_fence(content)]
    extracted = _extract_first_json_object(content)
    if extracted is not None:
        return extracted

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise json.JSONDecodeError("Could not parse JSON object from response", content, 0)


def _extract_legacy_score(content: str) -> float | None:
    for pattern in (LEGACY_FINAL_SCORE_RE, PLAIN_SCORE_RE):
        match = pattern.search(content)
        if match:
            value = _coerce_number(match.group(1))
            if value is not None:
                return _clip_score(value, minimum=0.0, maximum=100.0)
    return None


def _normalize_structured_image_response(parsed: dict[str, Any]) -> dict[str, Any]:
    if all(key in parsed for key in LEGACY_BOOLEAN_FIELDS):
        subscores = {
            target_key: 25 if bool(parsed.get(source_key, False)) else 0
            for source_key, target_key in LEGACY_BOOLEAN_FIELDS.items()
        }
        return {
            "analysis": {},
            "subscores": subscores,
            "score": float(sum(subscores.values())),
            "confidence": None,
            "reason": str(parsed.get("reason", "")) if parsed.get("reason") is not None else "",
            "protocol": "legacy_boolean_json",
        }

    subscores_raw = parsed.get("subscores")
    normalized_subscores: dict[str, int] | None = None
    if isinstance(subscores_raw, dict):
        normalized_subscores = {}
        for field in IMAGE_SCORE_FIELDS:
            raw_value = _coerce_number(subscores_raw.get(field, 0))
            normalized_subscores[field] = int(round(_clip_score(raw_value or 0.0, minimum=0.0, maximum=25.0)))

    score_value = _coerce_number(parsed.get("score"))
    if normalized_subscores is None and score_value is None:
        raise ValueError("Image judge response is missing both `subscores` and `score`")

    if normalized_subscores is None:
        normalized_subscores = {field: 0 for field in IMAGE_SCORE_FIELDS}
        final_score = _clip_score(score_value or 0.0, minimum=0.0, maximum=100.0)
        protocol = "score_only_json"
    else:
        subscore_total = float(sum(normalized_subscores.values()))
        final_score = _clip_score(subscore_total, minimum=0.0, maximum=100.0)
        protocol = "structured_json"

    confidence = _coerce_number(parsed.get("confidence"))
    normalized_confidence = None if confidence is None else _clip_score(confidence, minimum=0.0, maximum=1.0)
    analysis = parsed.get("analysis")
    normalized_analysis = analysis if isinstance(analysis, dict) else {}
    reason = parsed.get("reason")
    normalized_reason = str(reason) if reason is not None else ""

    return {
        "analysis": normalized_analysis,
        "subscores": normalized_subscores,
        "score": final_score,
        "confidence": normalized_confidence,
        "reason": normalized_reason,
        "protocol": protocol,
    }


def _parse_image_judge_response(content: str) -> dict[str, Any]:
    try:
        parsed = _parse_json_object_from_text(content)
    except json.JSONDecodeError:
        legacy_score = _extract_legacy_score(content)
        if legacy_score is not None:
            return {
                "analysis": {},
                "subscores": {field: 0 for field in IMAGE_SCORE_FIELDS},
                "score": legacy_score,
                "confidence": None,
                "reason": "Parsed legacy final score output.",
                "protocol": "legacy_final_score",
            }
        raise
    return _normalize_structured_image_response(parsed)


def _parse_text_judge_response(content: str) -> dict[str, Any]:
    return _parse_json_object_from_text(content)


def _completion_metrics(result) -> dict[str, Any]:
    metrics = {"duration_seconds": result.duration_seconds}
    metrics.update({key: value for key, value in result.usage.items() if value is not None})
    return metrics


# ---------------------------------------------------------------------------
# Pixel similarity fallback
# ---------------------------------------------------------------------------

def pixel_score(pred: Image.Image, gold: Image.Image) -> float:
    """
    Deterministic pixel-level similarity score in [0, 100].

    Weighted combination of:
    - PSNR (60%): normalized assuming typical range [20, 40] dB.
    - Pearson correlation on grayscale (40%): normalized to [0, 100].
    """
    pred_rgb = pred.resize(gold.size, Image.LANCZOS).convert("RGB")
    p = np.asarray(pred_rgb, dtype=np.float32)
    g = np.asarray(gold.convert("RGB"), dtype=np.float32)

    mse = float(np.mean((p - g) ** 2))
    if mse < 1e-6:
        psnr_score = 100.0
    else:
        psnr = 20.0 * np.log10(255.0 / np.sqrt(mse))
        psnr_score = float(min(100.0, max(0.0, (psnr - 20.0) * 5.0)))

    pf = p.mean(axis=2).flatten()
    gf = g.mean(axis=2).flatten()
    if pf.std() > 0 and gf.std() > 0:
        corr = float(np.corrcoef(pf, gf)[0, 1])
    else:
        corr = 1.0 if np.allclose(pf, gf) else 0.0
    corr_score = max(0.0, corr) * 100.0

    return 0.6 * psnr_score + 0.4 * corr_score


# ---------------------------------------------------------------------------
# Image judge
# ---------------------------------------------------------------------------

def judge_image_once(
    pred: Image.Image,
    gold: Image.Image,
    *,
    prompt: str | None = None,
    rubric_supplement: str | None = None,
    sample_index: int | None = None,
    temperature: float = DEFAULT_IMAGE_JUDGE_TEMPERATURE,
    max_tokens: int = DEFAULT_IMAGE_JUDGE_MAX_TOKENS,
) -> JudgeImageSample | None:
    """
    Execute one image-judge sample and return a structured score sample.

    `prompt` is a temporary compatibility escape hatch for older task-local graders.
    New code should prefer `rubric_supplement`.
    """
    model = _resolve_model(ENV_JUDGE_IMAGE_MODEL, DEFAULT_JUDGE_IMAGE_MODEL)
    kwargs = _get_litellm_kwargs(model)
    if not kwargs.get("api_key"):
        logger.debug("[judge_image_once] JUDGE_IMAGE_MODEL has no api_key, skipping.")
        return None

    legacy_prompt = _looks_like_legacy_prompt(prompt)
    user_prompt = prompt or _build_image_prompt(rubric_supplement)
    pred_b64 = _encode_pil(pred)
    gold_b64 = _encode_pil(gold)
    response_format = None if legacy_prompt or not _supports_response_format(model) else {"type": "json_object"}

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{pred_b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{gold_b64}"}},
        ],
    }]

    try:
        result = completion_with_observability(
            model=model,
            provider=kwargs.get("custom_llm_provider"),
            api_base=kwargs.get("api_base"),
            api_key=kwargs.get("api_key"),
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mode="json" if response_format is not None else "text",
            extra_tags={
                "judge_kind": "image",
                "judge_sample_index": sample_index,
                "judge_protocol": "legacy_prompt" if legacy_prompt else "structured_json",
            },
        )
    except Exception as exc:
        logger.warning("[judge_image_once] call failed (%s: %s).", type(exc).__name__, exc)
        return None

    try:
        response_content = extract_response_content(result.response)
        normalized = _parse_image_judge_response(response_content)
    except Exception as exc:
        emit_llm_event_sync(
            "llm.validation.failed",
            "Validation failed for LLM response",
            llm_context=result.llm_context,
            payloads={"response_text": ("response_body", response_content if "response_content" in locals() else "")},
            tags={"judge_kind": "image", "judge_sample_index": sample_index},
            error={"type": type(exc).__name__, "message": str(exc)},
        )
        emit_llm_event_sync(
            "llm.call.failed",
            "LLM call failed",
            llm_context=result.llm_context,
            payloads={"error_body": ("error_body", {"message": str(exc), "repr": repr(exc)})},
            metrics={"duration_seconds": result.duration_seconds},
            tags={"judge_kind": "image", "judge_sample_index": sample_index},
            error={"type": type(exc).__name__, "message": str(exc)},
        )
        logger.warning("[judge_image_once] validation failed (%s: %s).", type(exc).__name__, exc)
        return None

    sample = JudgeImageSample(
        score=float(normalized["score"]),
        confidence=normalized["confidence"],
        reason=str(normalized["reason"]),
        protocol=str(normalized["protocol"]),
        normalized=normalized,
        duration_seconds=result.duration_seconds,
        usage=result.usage,
    )
    emit_llm_event_sync(
        "llm.response.validated",
        "Image judge response validated",
        llm_context=result.llm_context,
        payloads={"judge_result": ("judge_result", normalized)},
        metrics={"judge_score": sample.score},
        tags={
            "judge_kind": "image",
            "judge_protocol": sample.protocol,
            "judge_sample_index": sample_index,
            "judge_confidence": sample.confidence,
        },
    )
    emit_llm_event_sync(
        "llm.call.completed",
        "LLM call completed",
        llm_context=result.llm_context,
        metrics={**_completion_metrics(result), "judge_score": sample.score},
        tags={
            "judge_kind": "image",
            "judge_protocol": sample.protocol,
            "judge_sample_index": sample_index,
            "judge_confidence": sample.confidence,
        },
    )
    logger.debug(
        "[judge_image_once] sample=%s score=%.1f protocol=%s reason=%s",
        sample_index,
        sample.score,
        sample.protocol,
        sample.reason,
    )
    return sample


def vlm_score(
    pred: Image.Image,
    gold: Image.Image,
    *,
    prompt: str | None = None,
    rubric_supplement: str | None = None,
    sample_index: int | None = None,
    temperature: float = DEFAULT_IMAGE_JUDGE_TEMPERATURE,
    max_tokens: int = DEFAULT_IMAGE_JUDGE_MAX_TOKENS,
) -> float | None:
    """
    Backward-compatible single-sample image judge.

    New image grading should prefer `judge_image()` for multi-sample aggregation.
    """
    sample = judge_image_once(
        pred,
        gold,
        prompt=prompt,
        rubric_supplement=rubric_supplement,
        sample_index=sample_index,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return None if sample is None else sample.score


def judge_image(
    pred: Image.Image,
    gold: Image.Image,
    *,
    threshold: float = 60.0,
    prompt: str | None = None,
    rubric_supplement: str | None = None,
    num_samples: int = DEFAULT_IMAGE_JUDGE_SAMPLES,
    min_valid_samples: int = DEFAULT_IMAGE_JUDGE_MIN_VALID_SAMPLES,
    allow_pixel_fallback: bool = True,
) -> float:
    """
    Grade an image submission against a gold reference.

    Strategy:
    1. Run multiple VLM judge samples.
    2. Average valid structured scores.
    3. Fall back to pixel scoring only when judge evidence is insufficient.

    `prompt` remains a temporary compatibility escape hatch for older task-local graders.
    New code should prefer `rubric_supplement`.
    """
    valid_samples: list[JudgeImageSample] = []
    for sample_index in range(1, max(1, num_samples) + 1):
        sample = judge_image_once(
            pred,
            gold,
            prompt=prompt,
            rubric_supplement=rubric_supplement,
            sample_index=sample_index,
        )
        if sample is None:
            continue
        valid_samples.append(sample)
        emit_runtime_event(
            "judge.image.sample.completed",
            "Image judge sample completed",
            tags={
                "protocol": sample.protocol,
                "sample_index": sample_index,
            },
            metrics={
                "score": sample.score,
                "confidence": sample.confidence,
                "duration_seconds": sample.duration_seconds,
            },
        )

    if len(valid_samples) >= max(1, min_valid_samples):
        final_score = float(np.mean([sample.score for sample in valid_samples]))
        source = "vlm_mean"
    elif valid_samples and not allow_pixel_fallback:
        final_score = float(np.mean([sample.score for sample in valid_samples]))
        source = "vlm_single_low_confidence"
    elif allow_pixel_fallback:
        final_score = pixel_score(pred, gold)
        source = "pixel_fallback"
    else:
        final_score = 0.0
        source = "judge_unavailable"

    aggregate = JudgeImageAggregate(
        final_score=float(_clip_score(final_score, minimum=0.0, maximum=100.0)),
        sample_scores=tuple(sample.score for sample in valid_samples),
        valid_samples=len(valid_samples),
        total_samples=max(1, num_samples),
        source=source,
    )
    passed = aggregate.final_score >= threshold
    emit_runtime_event(
        "judge.image.aggregate.completed",
        "Aggregated image judge samples",
        tags={
            "source": aggregate.source,
            "passed": passed,
            "threshold": threshold,
            "legacy_prompt": bool(prompt and _looks_like_legacy_prompt(prompt)),
        },
        metrics={
            "samples_total": aggregate.total_samples,
            "samples_valid": aggregate.valid_samples,
            "final_score": aggregate.final_score,
            "sample_scores": list(aggregate.sample_scores),
        },
    )
    logger.info(
        "[judge_image] source=%s score=%.1f threshold=%.1f passed=%s valid=%d/%d sample_scores=%s",
        aggregate.source,
        aggregate.final_score,
        threshold,
        passed,
        aggregate.valid_samples,
        aggregate.total_samples,
        list(aggregate.sample_scores),
    )
    return 1.0 if passed else 0.0


# ---------------------------------------------------------------------------
# Text judge
# ---------------------------------------------------------------------------

def text_score(
    pred: str,
    gold: str,
    *,
    criteria: str | None = None,
    system_prompt: str | None = None,
) -> float | None:
    """
    Call the text LLM judge (JUDGE_MODEL) to score a predicted answer.
    """
    model = _resolve_model(ENV_JUDGE_MODEL, DEFAULT_JUDGE_MODEL)
    kwargs = _get_litellm_kwargs(model)
    if not kwargs.get("api_key"):
        logger.debug("[text_score] JUDGE_MODEL has no api_key, skipping.")
        return None

    system = system_prompt or DEFAULT_TEXT_JUDGE_SYSTEM
    crit = criteria or DEFAULT_TEXT_JUDGE_CRITERIA
    user_prompt = (
        f"Evaluation criteria: {crit}\n\n"
        f"Gold answer:\n{gold}\n\n"
        f"Predicted answer:\n{pred}\n\n"
        "Score the predicted answer (0-100)."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]

    try:
        result = completion_with_observability(
            model=model,
            provider=kwargs.get("custom_llm_provider"),
            api_base=kwargs.get("api_base"),
            api_key=kwargs.get("api_key"),
            messages=messages,
            temperature=0.0,
            max_tokens=128,
            response_mode="json",
            extra_tags={"judge_kind": "text"},
        )
    except Exception as exc:
        logger.warning("[text_score] call failed (%s: %s).", type(exc).__name__, exc)
        return None

    try:
        response_content = extract_response_content(result.response)
        parsed = _parse_text_judge_response(response_content)
        score = float(parsed["score"])
    except Exception as exc:
        emit_llm_event_sync(
            "llm.validation.failed",
            "Validation failed for LLM response",
            llm_context=result.llm_context,
            payloads={"response_text": ("response_body", response_content if "response_content" in locals() else "")},
            error={"type": type(exc).__name__, "message": str(exc)},
        )
        emit_llm_event_sync(
            "llm.call.failed",
            "LLM call failed",
            llm_context=result.llm_context,
            payloads={"error_body": ("error_body", {"message": str(exc), "repr": repr(exc)})},
            metrics={"duration_seconds": result.duration_seconds},
            error={"type": type(exc).__name__, "message": str(exc)},
        )
        logger.warning("[text_score] call failed (%s: %s).", type(exc).__name__, exc)
        return None

    emit_llm_event_sync(
        "llm.response.validated",
        "JSON response validated",
        llm_context=result.llm_context,
    )
    emit_llm_event_sync(
        "llm.call.completed",
        "LLM call completed",
        llm_context=result.llm_context,
        metrics=_completion_metrics(result),
    )
    logger.debug("[text_score] score=%.1f reason=%s", score, parsed.get("reason", ""))
    return max(0.0, min(100.0, score))


def judge_text(
    pred: str,
    gold: str,
    *,
    criteria: str | None = None,
    system_prompt: str | None = None,
    threshold: float = 60.0,
) -> float:
    """
    Grade a text submission against a gold reference.
    """
    score = text_score(pred, gold, criteria=criteria, system_prompt=system_prompt)
    if score is None:
        logger.warning("[judge_text] Judge unavailable, returning 0.0.")
        return 0.0
    passed = score >= threshold
    logger.info("[judge_text] score=%.1f threshold=%.1f passed=%s", score, threshold, passed)
    return 1.0 if passed else 0.0


__all__ = [
    "DEFAULT_IMAGE_JUDGE_PROMPT",
    "DEFAULT_TEXT_JUDGE_CRITERIA",
    "DEFAULT_TEXT_JUDGE_SYSTEM",
    "ENV_JUDGE_IMAGE_MODEL",
    "ENV_JUDGE_MODEL",
    "JudgeImageAggregate",
    "JudgeImageSample",
    "judge_image",
    "judge_image_once",
    "judge_text",
    "pixel_score",
    "text_score",
    "vlm_score",
]
