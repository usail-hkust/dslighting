"""
LLM-as-judge utilities for benchmark grading.

Two judge types are supported:
- Image judge : uses a VLM (JUDGE_IMAGE_MODEL) to compare two scientific plots.
- Text judge  : uses a text LLM (JUDGE_MODEL) to evaluate free-form text or code output.

Model configuration is resolved from environment variables:
    JUDGE_MODEL=<model_name>        # text judge  (must exist in LLM_MODEL_CONFIGS)
    JUDGE_IMAGE_MODEL=<model_name>  # image judge (must be a VLM in LLM_MODEL_CONFIGS)

Both env vars expect model names matching keys in LLM_MODEL_CONFIGS so that
api_key / api_base are resolved automatically.

Default prompts live here as module-level constants.
Callers (grade.py) can override them via the ``prompt`` / ``system_prompt`` parameters
to tailor evaluation for a specific task.

Fallback behaviour:
- Image judge falls back to pixel-similarity when the VLM call fails.
- Text judge returns 0.0 when the LLM call fails.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from typing import Any

import numpy as np
from PIL import Image

from dslighting.core.config.llm_resolution import load_model_override_map

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
# Default prompts  (ownership can move to grade.py via the prompt= parameter)
# ---------------------------------------------------------------------------

DEFAULT_IMAGE_JUDGE_PROMPT = """\
You are evaluating two scientific visualization plots.
The FIRST image is the predicted plot. The SECOND image is the gold reference.

Answer strictly in JSON with exactly these 4 boolean fields:
{
  "same_type": true/false,       // same chart type (line / bar / scatter / heatmap / ...)
  "correct_axes": true/false,    // axis labels and represented variables match
  "correct_pattern": true/false, // data trends and relative magnitudes are consistent
  "correct_style": true/false    // colors and legend categories are consistent
}
Output only the JSON object, nothing else."""

DEFAULT_TEXT_JUDGE_SYSTEM = """\
You are an expert evaluator for data science and scientific tasks.
Score the predicted answer against the gold reference based on the provided criteria.
Output strictly a JSON object: {"score": <integer 0-100>, "reason": "<one sentence>"}
Nothing else."""

DEFAULT_TEXT_JUDGE_CRITERIA = "correctness, completeness, and accuracy"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_model(env_var: str, default: str) -> str:
    return os.environ.get(env_var, "").strip() or default


def _get_litellm_kwargs(model: str) -> dict[str, Any]:
    """Build litellm call kwargs by looking up model in LLM_MODEL_CONFIGS."""
    config = load_model_override_map().get(model, {})
    kwargs: dict[str, Any] = {"model": model}

    # api_keys (list) takes priority over api_key (str); pick first key
    api_keys = config.get("api_keys")
    api_key = config.get("api_key")
    if api_keys:
        kwargs["api_key"] = api_keys[0]
    elif api_key:
        kwargs["api_key"] = api_key

    if config.get("api_base"):
        kwargs["api_base"] = config["api_base"]

    return kwargs


def _encode_pil(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _parse_json_response(content: str) -> dict:
    """Strip optional markdown fences and parse JSON."""
    text = content.strip()
    if text.startswith("```"):
        parts = text.split("```")
        # parts[1] is the fenced block, possibly starting with "json\n"
        text = parts[1].lstrip("json").strip()
    return json.loads(text)


# ---------------------------------------------------------------------------
# Pixel similarity fallback
# ---------------------------------------------------------------------------

def pixel_score(pred: Image.Image, gold: Image.Image) -> float:
    """
    Deterministic pixel-level similarity score in [0, 100].

    Weighted combination of:
    - PSNR (60 %): normalised assuming typical range [20, 40] dB.
    - Pearson correlation on grayscale (40 %): normalised to [0, 100].
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

def vlm_score(
    pred: Image.Image,
    gold: Image.Image,
    *,
    prompt: str | None = None,
) -> float | None:
    """
    Call the VLM judge (JUDGE_IMAGE_MODEL) to compare two images.

    Args:
        pred:   Predicted image.
        gold:   Gold reference image.
        prompt: Custom user prompt. Defaults to DEFAULT_IMAGE_JUDGE_PROMPT.
                Override this in grade.py to tailor evaluation for a specific task.

    Returns:
        Score in [0, 100] (each of 4 criteria worth 25 pts), or None on failure.
    """
    model = _resolve_model(ENV_JUDGE_IMAGE_MODEL, DEFAULT_JUDGE_IMAGE_MODEL)
    kwargs = _get_litellm_kwargs(model)
    if not kwargs.get("api_key"):
        logger.debug("[vlm_score] JUDGE_IMAGE_MODEL has no api_key, skipping.")
        return None

    user_prompt = prompt or DEFAULT_IMAGE_JUDGE_PROMPT
    pred_b64 = _encode_pil(pred)
    gold_b64 = _encode_pil(gold)

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{pred_b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{gold_b64}"}},
        ],
    }]

    try:
        import litellm
        response = litellm.completion(
            **kwargs,
            messages=messages,
            max_tokens=64,
            temperature=0.0,
        )
        parsed = _parse_json_response(response.choices[0].message.content)
        score = sum([
            bool(parsed.get("same_type", False)),
            bool(parsed.get("correct_axes", False)),
            bool(parsed.get("correct_pattern", False)),
            bool(parsed.get("correct_style", False)),
        ]) / 4.0 * 100.0
        logger.debug("[vlm_score] score=%.1f parsed=%s", score, parsed)
        return score
    except Exception as exc:
        logger.warning("[vlm_score] call failed (%s: %s), will fallback to pixel.", type(exc).__name__, exc)
        return None


def judge_image(
    pred: Image.Image,
    gold: Image.Image,
    *,
    threshold: float = 60.0,
    prompt: str | None = None,
) -> float:
    """
    Grade an image submission against a gold reference.

    Strategy:
      1. VLM judge via JUDGE_IMAGE_MODEL.
      2. Falls back to pixel_score if VLM is unavailable or fails.

    Args:
        pred:      Predicted image.
        gold:      Gold reference image.
        threshold: Minimum score to pass (default 60).
        prompt:    Optional custom prompt forwarded to vlm_score.
                   Define this in your grade.py for task-specific evaluation.

    Returns:
        1.0 if score >= threshold, else 0.0.
    """
    score = vlm_score(pred, gold, prompt=prompt)
    source = "vlm"
    if score is None:
        score = pixel_score(pred, gold)
        source = "pixel"
    passed = score >= threshold
    logger.info("[judge_image] source=%s score=%.1f threshold=%.1f passed=%s", source, score, threshold, passed)
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

    Args:
        pred:          Predicted text / answer.
        gold:          Gold reference text.
        criteria:      Evaluation criteria description.
                       Defaults to DEFAULT_TEXT_JUDGE_CRITERIA.
                       Override in grade.py for task-specific evaluation.
        system_prompt: Custom system prompt. Defaults to DEFAULT_TEXT_JUDGE_SYSTEM.
                       Override in grade.py for full prompt control.

    Returns:
        Score in [0, 100], or None on failure.
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

    try:
        import litellm
        response = litellm.completion(
            **kwargs,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=128,
            temperature=0.0,
        )
        parsed = _parse_json_response(response.choices[0].message.content)
        score = float(parsed["score"])
        logger.debug("[text_score] score=%.1f reason=%s", score, parsed.get("reason", ""))
        return max(0.0, min(100.0, score))
    except Exception as exc:
        logger.warning("[text_score] call failed (%s: %s).", type(exc).__name__, exc)
        return None


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

    Args:
        pred:          Predicted text.
        gold:          Gold reference text.
        criteria:      Evaluation criteria. Define in grade.py for task-specific use.
        system_prompt: Override system prompt. Define in grade.py for full control.
        threshold:     Minimum score to pass (default 60).

    Returns:
        1.0 if score >= threshold, else 0.0.
        Returns 0.0 if the judge call fails entirely.
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
    "judge_image",
    "judge_text",
    "pixel_score",
    "text_score",
    "vlm_score",
]
