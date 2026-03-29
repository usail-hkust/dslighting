"""
LLM-as-judge utilities for benchmark grading.

Two judge types are supported:
- Image judge: uses a VLM (JUDGE_IMAGE_MODEL) to compare scientific plots.
- Text judge: uses a text LLM (JUDGE_MODEL) to evaluate free-form text or code output.

Model configuration is resolved through the shared role-based LLM resolver.
Role-scoped environment variables remain supported:
    JUDGE_MODEL=<model_name>        # text judge
    JUDGE_IMAGE_MODEL=<model_name>  # image judge

The image-judge protocol is structured JSON with rubric-based subscores.
Older prompt formats and legacy score parsing are no longer supported.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import io
import json
import logging
from typing import Any

import numpy as np
from PIL import Image

from dslighting.core.config.llm_roles import (
    ENV_JUDGE_IMAGE_MODEL,
    ENV_JUDGE_MODEL,
    resolve_image_judge_llm_config,
    resolve_text_judge_llm_config,
)
from dslighting.logging.events import emit_runtime_event
from dslighting.services.llm.observed_call import (
    completion_with_observability,
    emit_llm_event_sync,
    extract_response_content,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Image-judge protocol defaults
# ---------------------------------------------------------------------------
IMAGE_SCORE_FIELDS = (
    "chart_type",
    "axes_semantics",
    "pattern_fidelity",
    "style_legend",
)
DEFAULT_IMAGE_JUDGE_SAMPLES = 3
DEFAULT_IMAGE_JUDGE_MIN_VALID_SAMPLES = 2
DEFAULT_IMAGE_JUDGE_MAX_TOKENS = 256
DEFAULT_IMAGE_JUDGE_TEMPERATURE = 0.2
DEFAULT_IMAGE_JUDGE_MAX_IMAGE_SIDE = 1280
JSON_MODE_UNSUPPORTED_MARKERS = (
    "json mode is not supported",
    "json mode not supported",
    "response_format is not supported",
    "response_format not supported",
    "json_object is not supported",
)
_JSON_MODE_UNSUPPORTED_CAPABILITIES: set[tuple[str, str | None, str | None]] = set()
RETRYABLE_PROVIDER_ERROR_MARKERS = (
    "internalservererror",
    "service unavailable",
    "temporarily unavailable",
    "request processing failed",
    "timeout",
    "timed out",
    "connection error",
    "connection reset",
    "remoteprotocolerror",
    "ratelimit",
    "rate limit",
)

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

The first character of your response must be {.
The last character of your response must be }.
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
    planned_samples: int
    source: str


@dataclass(frozen=True)
class JudgeImageFailure:
    kind: str
    request_mode: str
    error_type: str
    error_message: str
    abort_remaining: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _llm_config_to_call_kwargs(config: Any) -> dict[str, Any]:
    """Convert a resolved shared LLM config into direct LiteLLM call kwargs."""
    api_keys = config.get_api_keys()
    return {
        "model": config.model,
        "api_key": api_keys[0] if api_keys else None,
        "api_base": config.api_base,
        "provider": config.provider,
    }


def _prepare_judge_image(img: Image.Image) -> Image.Image:
    prepared = img.convert("RGB")
    width, height = prepared.size
    longest_side = max(width, height)
    if longest_side <= DEFAULT_IMAGE_JUDGE_MAX_IMAGE_SIDE:
        return prepared
    scale = DEFAULT_IMAGE_JUDGE_MAX_IMAGE_SIDE / float(longest_side)
    resized = prepared.resize(
        (
            max(1, int(round(width * scale))),
            max(1, int(round(height * scale))),
        ),
        Image.LANCZOS,
    )
    return resized


def _encode_pil(img: Image.Image) -> str:
    buf = io.BytesIO()
    _prepare_judge_image(img).save(buf, format="PNG", optimize=True, compress_level=9)
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


def _json_mode_capability_key(
    *,
    model: str,
    provider: str | None,
    api_base: str | None,
) -> tuple[str, str | None, str | None]:
    return (model.strip().lower(), (provider or "").strip().lower() or None, (api_base or "").strip().lower() or None)


def _is_json_mode_unsupported_cached(
    *,
    model: str,
    provider: str | None,
    api_base: str | None,
) -> bool:
    return _json_mode_capability_key(model=model, provider=provider, api_base=api_base) in _JSON_MODE_UNSUPPORTED_CAPABILITIES


def _mark_json_mode_unsupported(
    *,
    model: str,
    provider: str | None,
    api_base: str | None,
) -> None:
    _JSON_MODE_UNSUPPORTED_CAPABILITIES.add(
        _json_mode_capability_key(model=model, provider=provider, api_base=api_base)
    )


def _is_json_mode_unsupported_error(exc: Exception) -> bool:
    message = str(exc).lower()
    if "json mode" in message and "not supported" in message:
        return True
    if "response_format" in message and ("not supported" in message or "unsupported" in message):
        return True
    if "response_format" in message and "invalid parameter" in message:
        return True
    return any(marker in message for marker in JSON_MODE_UNSUPPORTED_MARKERS)


def _is_retryable_provider_error(exc: Exception) -> bool:
    try:
        import litellm.exceptions as litellm_exceptions
    except ImportError:
        litellm_exceptions = None

    if litellm_exceptions is not None:
        retryable_errors = (
            litellm_exceptions.RateLimitError,
            litellm_exceptions.ServiceUnavailableError,
            litellm_exceptions.Timeout,
            litellm_exceptions.APIConnectionError,
            litellm_exceptions.InternalServerError,
        )
        if isinstance(exc, retryable_errors):
            return True

        fail_fast_errors = (
            litellm_exceptions.InvalidRequestError,
            litellm_exceptions.NotFoundError,
            litellm_exceptions.AuthenticationError,
            litellm_exceptions.PermissionDeniedError,
        )
        if isinstance(exc, fail_fast_errors):
            return False

    if _is_json_mode_unsupported_error(exc):
        return False

    message = str(exc).lower()
    return any(marker in message for marker in RETRYABLE_PROVIDER_ERROR_MARKERS)


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


def _normalize_structured_image_response(parsed: dict[str, Any]) -> dict[str, Any]:
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
    parsed = _parse_json_object_from_text(content)
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
    rubric_supplement: str | None = None,
    sample_index: int | None = None,
    temperature: float = DEFAULT_IMAGE_JUDGE_TEMPERATURE,
    max_tokens: int = DEFAULT_IMAGE_JUDGE_MAX_TOKENS,
) -> JudgeImageSample | JudgeImageFailure | None:
    """
    Execute one image-judge sample and return a structured score sample.

    The judge always uses the structured JSON image protocol.
    """
    resolved_config = resolve_image_judge_llm_config()
    kwargs = _llm_config_to_call_kwargs(resolved_config)
    model = kwargs["model"]
    if not kwargs.get("api_key"):
        logger.debug("[judge_image_once] JUDGE_IMAGE_MODEL has no api_key, skipping.")
        return JudgeImageFailure(
            kind="judge_unconfigured",
            request_mode="unconfigured",
            error_type="MissingApiKey",
            error_message="JUDGE_IMAGE_MODEL has no api_key configured.",
            abort_remaining=True,
        )

    user_prompt = _build_image_prompt(rubric_supplement)
    pred_b64 = _encode_pil(pred)
    gold_b64 = _encode_pil(gold)
    provider = kwargs.get("provider")
    api_base = kwargs.get("api_base")
    json_mode_enabled = (
        _supports_response_format(model)
        and not _is_json_mode_unsupported_cached(model=model, provider=provider, api_base=api_base)
    )

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{pred_b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{gold_b64}"}},
        ],
    }]

    def _call_once(*, use_json_mode: bool, retry_reason: str | None = None):
        response_format = {"type": "json_object"} if use_json_mode else None
        request_mode = "json_mode" if use_json_mode else "prompt_enforced_json"
        return completion_with_observability(
            model=model,
            provider=provider,
            api_base=api_base,
            api_key=kwargs.get("api_key"),
            messages=messages,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mode="json" if response_format is not None else "text",
            extra_tags={
                "judge_kind": "image",
                "judge_sample_index": sample_index,
                "judge_request_mode": request_mode,
                "judge_retry_reason": retry_reason,
            },
        )

    request_mode_used = "prompt_enforced_json"
    try:
        request_mode_used = "json_mode" if json_mode_enabled else "prompt_enforced_json"
        result = _call_once(use_json_mode=json_mode_enabled)
    except Exception as exc:
        if json_mode_enabled and _is_json_mode_unsupported_error(exc):
            _mark_json_mode_unsupported(model=model, provider=provider, api_base=api_base)
            logger.info(
                "[judge_image_once] json mode unsupported for model=%s provider=%s api_base=%s; retrying with prompt-enforced JSON.",
                model,
                provider or "unknown",
                api_base or "unknown",
            )
            try:
                request_mode_used = "prompt_enforced_json"
                result = _call_once(use_json_mode=False, retry_reason="json_mode_unsupported")
            except Exception as retry_exc:
                logger.warning("[judge_image_once] call failed (%s: %s).", type(retry_exc).__name__, retry_exc)
                return JudgeImageFailure(
                    kind="provider_transport_error" if _is_retryable_provider_error(retry_exc) else "call_failed",
                    request_mode=request_mode_used,
                    error_type=type(retry_exc).__name__,
                    error_message=str(retry_exc),
                    abort_remaining=_is_retryable_provider_error(retry_exc),
                )
        else:
            logger.warning("[judge_image_once] call failed (%s: %s).", type(exc).__name__, exc)
            return JudgeImageFailure(
                kind="provider_transport_error" if _is_retryable_provider_error(exc) else "call_failed",
                request_mode=request_mode_used,
                error_type=type(exc).__name__,
                error_message=str(exc),
                abort_remaining=_is_retryable_provider_error(exc),
            )

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
        return JudgeImageFailure(
            kind="validation_failed",
            request_mode=request_mode_used,
            error_type=type(exc).__name__,
            error_message=str(exc),
            abort_remaining=False,
        )

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
            "judge_request_mode": request_mode_used,
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
            "judge_request_mode": request_mode_used,
        },
    )
    logger.debug(
        "[judge_image_once] sample=%s score=%.1f protocol=%s request_mode=%s reason=%s",
        sample_index,
        sample.score,
        sample.protocol,
        request_mode_used,
        sample.reason,
    )
    return sample


def vlm_score(
    pred: Image.Image,
    gold: Image.Image,
    *,
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
        rubric_supplement=rubric_supplement,
        sample_index=sample_index,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return sample.score if isinstance(sample, JudgeImageSample) else None


def judge_image(
    pred: Image.Image,
    gold: Image.Image,
    *,
    threshold: float = 60.0,
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

    The judge always uses the structured JSON image protocol.
    """
    valid_samples: list[JudgeImageSample] = []
    planned_samples = max(1, num_samples)
    attempted_samples = 0
    stop_reason: str | None = None
    stopped_early = False
    for sample_index in range(1, planned_samples + 1):
        attempted_samples += 1
        attempt = judge_image_once(
            pred,
            gold,
            rubric_supplement=rubric_supplement,
            sample_index=sample_index,
        )
        if isinstance(attempt, JudgeImageSample):
            sample = attempt
            valid_samples.append(sample)
        else:
            failure = attempt
            if isinstance(failure, JudgeImageFailure) and failure.abort_remaining:
                stopped_early = True
                stop_reason = failure.kind
                logger.info(
                    "[judge_image] stopping early after sample=%s due to %s in request_mode=%s (%s: %s).",
                    sample_index,
                    failure.kind,
                    failure.request_mode,
                    failure.error_type,
                    failure.error_message,
                )
                break
            remaining_samples = planned_samples - sample_index
            max_possible_valid = len(valid_samples) + remaining_samples
            if allow_pixel_fallback and max_possible_valid < max(1, min_valid_samples):
                stopped_early = True
                stop_reason = "insufficient_remaining_samples"
                logger.info(
                    "[judge_image] stopping early after sample=%s because reaching min_valid_samples=%s is impossible (valid=%s remaining=%s).",
                    sample_index,
                    max(1, min_valid_samples),
                    len(valid_samples),
                    remaining_samples,
                )
                break
            continue
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
        remaining_samples = planned_samples - sample_index
        if remaining_samples > 0 and len(valid_samples) >= max(1, min_valid_samples):
            current_sum = float(sum(item.score for item in valid_samples))
            optimistic_mean = (current_sum + 100.0 * remaining_samples) / (len(valid_samples) + remaining_samples)
            pessimistic_mean = current_sum / (len(valid_samples) + remaining_samples)
            if optimistic_mean < threshold:
                stopped_early = True
                stop_reason = "threshold_unreachable"
                logger.info(
                    "[judge_image] stopping early after sample=%s because threshold=%.1f is unreachable (optimistic_mean=%.1f).",
                    sample_index,
                    threshold,
                    optimistic_mean,
                )
                break
            if pessimistic_mean >= threshold:
                stopped_early = True
                stop_reason = "threshold_already_secured"
                logger.info(
                    "[judge_image] stopping early after sample=%s because threshold=%.1f is already secured (pessimistic_mean=%.1f).",
                    sample_index,
                    threshold,
                    pessimistic_mean,
                )
                break

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
        total_samples=attempted_samples,
        planned_samples=planned_samples,
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
            "stopped_early": stopped_early,
            "stop_reason": stop_reason,
        },
        metrics={
            "samples_total": aggregate.total_samples,
            "samples_planned": aggregate.planned_samples,
            "samples_valid": aggregate.valid_samples,
            "final_score": aggregate.final_score,
            "sample_scores": list(aggregate.sample_scores),
        },
    )
    logger.info(
        "[judge_image] source=%s score=%.1f threshold=%.1f passed=%s valid=%d attempted=%d planned=%d sample_scores=%s",
        aggregate.source,
        aggregate.final_score,
        threshold,
        passed,
        aggregate.valid_samples,
        aggregate.total_samples,
        aggregate.planned_samples,
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
    resolved_config = resolve_text_judge_llm_config()
    kwargs = _llm_config_to_call_kwargs(resolved_config)
    model = kwargs["model"]
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
            provider=kwargs.get("provider"),
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
