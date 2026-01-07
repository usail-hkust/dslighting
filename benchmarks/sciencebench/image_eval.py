"""
Utility helpers for grading ScienceBench visualization tasks.

These helpers attempt to mirror the original ScienceAgentBench evaluation
logic that relies on the optional `gpt4_visual_judge` package. When that
dependency is unavailable, we fall back to a simple pixel-level similarity
metric (1 - MSE) so that grading can still proceed deterministically during
local development and CI.
"""

from __future__ import annotations

import base64
import contextlib
import io
import os
import tempfile
from typing import Optional

import numpy as np
from PIL import Image

try:  # Optional dependency – only available in the original benchmark
    from gpt4_visual_judge import encode_image as _encode_image, score_figure as _score_figure  # type: ignore
    _VISUAL_JUDGE_AVAILABLE = True
except Exception:  # pragma: no cover - dependency not bundled
    _encode_image = None
    _score_figure = None
    _VISUAL_JUDGE_AVAILABLE = False


def _load_image_from_base64(image_base64: str) -> Image.Image:
    if not isinstance(image_base64, str) or not image_base64.strip():
        raise ValueError("Empty image_base64 value")
    buffer = io.BytesIO(base64.b64decode(image_base64))
    return Image.open(buffer).convert("RGB")


def _score_with_visual_judge(pred_image: Image.Image, gold_image: Image.Image) -> Optional[float]:
    """
    Run the optional GPT-4 based visual judge if it is available.

    Returns:
        Score in [0, 100] when the judge is available, otherwise ``None``.
    """
    if not _VISUAL_JUDGE_AVAILABLE:
        return None

    pred_fd = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    gold_fd = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        pred_image.save(pred_fd.name, format="PNG")
        gold_image.save(gold_fd.name, format="PNG")

        pred_fig = _encode_image(pred_fd.name)  # type: ignore[arg-type]
        gold_fig = _encode_image(gold_fd.name)  # type: ignore[arg-type]
        full_response, score = _score_figure(pred_fig, gold_fig)  # type: ignore[misc]

        print(f"[visual_judge] score={score} response={full_response[:200]}...")
        return float(score)
    finally:
        pred_fd.close()
        gold_fd.close()
        with contextlib.suppress(OSError):
            os.unlink(pred_fd.name)
        with contextlib.suppress(OSError):
            os.unlink(gold_fd.name)


def _fallback_similarity(pred_image: Image.Image, gold_image: Image.Image) -> float:
    """
    Compute a deterministic similarity proxy in the absence of GPT-4 judging.

    Returns a value in [0, 1], where 1 represents identical images.
    """
    pred_resized = pred_image.resize(gold_image.size)
    gold_arr = np.asarray(gold_image, dtype=np.float32) / 255.0
    pred_arr = np.asarray(pred_resized, dtype=np.float32) / 255.0
    mse = float(np.mean((gold_arr - pred_arr) ** 2))
    similarity = max(0.0, 1.0 - mse)
    print(f"[fallback_similarity] similarity={similarity:.4f} (1 - MSE)")
    return similarity


def grade_visual_rows(
    submission_rows,
    threshold_score: float = 60.0,
) -> float:
    """
    Grade visualization submissions represented as base64-encoded PNG rows.

    Args:
        submission_rows: Iterable of dict-like objects containing
            ``image_base64_pred`` and ``image_base64_gold`` fields.
        threshold_score: Minimum GPT-4 score (0-100 scale) required to pass.

    Returns:
        1.0 when all rows meet the required threshold, otherwise 0.0.
    """
    success_flags = []
    for row in submission_rows:
        pred_b64 = row.get("image_base64_pred")
        gold_b64 = row.get("image_base64_gold")
        pred_img = _load_image_from_base64(pred_b64)
        gold_img = _load_image_from_base64(gold_b64)

        judge_score = _score_with_visual_judge(pred_img, gold_img)
        if judge_score is not None:
            is_success = judge_score >= threshold_score
            print(f"[visual_judge] pass={is_success} threshold={threshold_score}")
        else:
            similarity = _fallback_similarity(pred_img, gold_img)
            is_success = similarity >= (threshold_score / 100.0)
            print(f"[fallback] pass={is_success} threshold={threshold_score / 100.0:.2f}")

        success_flags.append(is_success)

    return 1.0 if success_flags and all(success_flags) else 0.0
