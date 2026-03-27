"""
Utility helpers for grading ScienceBench visualization tasks.

Grading uses the LLM-as-judge infrastructure from
``dslighting.benchmark.grading.llm_judge``:

  - Primary  : VLM judge via ``JUDGE_IMAGE_MODEL`` (default: Qwen2.5-VL-72B).
  - Fallback : pixel-similarity (PSNR + Pearson correlation) when VLM is unavailable.

The ``grade_visual_rows`` function is the main entry point and retains its
original interface so existing callers are unaffected.
"""

from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image

from dslighting.benchmark.grading.llm_judge import judge_image, pixel_score, vlm_score


def _load_image_from_base64(image_base64: str) -> Image.Image:
    if not isinstance(image_base64, str) or not image_base64.strip():
        raise ValueError("Empty image_base64 value")
    return Image.open(io.BytesIO(base64.b64decode(image_base64))).convert("RGB")


def grade_visual_rows(
    submission_rows: Any,
    threshold_score: float = 60.0,
    prompt: str | None = None,
) -> float:
    """
    Grade visualization submissions represented as base64-encoded PNG rows.

    Each row must contain ``image_base64_pred`` and ``image_base64_gold`` fields.

    Strategy per row:
      1. VLM judge (JUDGE_IMAGE_MODEL).
      2. Pixel-similarity fallback if VLM unavailable or fails.

    Args:
        submission_rows: Iterable of dict-like objects with base64 image fields.
        threshold_score: Minimum score (0-100) required to pass (default 60).
        prompt:          Optional custom VLM prompt forwarded to ``judge_image``.
                         Define this in your grade.py for task-specific evaluation.

    Returns:
        1.0 when all rows meet the threshold, otherwise 0.0.
    """
    success_flags = []
    for row in submission_rows:
        pred_img = _load_image_from_base64(row.get("image_base64_pred"))
        gold_img = _load_image_from_base64(row.get("image_base64_gold"))

        result = judge_image(pred_img, gold_img, threshold=threshold_score, prompt=prompt)
        success_flags.append(result == 1.0)

    return 1.0 if success_flags and all(success_flags) else 0.0
