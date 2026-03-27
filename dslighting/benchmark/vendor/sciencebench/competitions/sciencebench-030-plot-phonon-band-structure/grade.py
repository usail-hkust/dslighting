"""
Grading for sciencebench-030-plot-phonon-band-structure (plot-phonon-band-structure) – visualization task.

Evaluation strategy:
  1. GPT-4V visual judge with prompt.
  2. Threshold: 60.0 / 100.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image

from dslighting.benchmark.grading import judge_image
from dslighting.benchmark.grading.models import GradingRequest

THRESHOLD = 60.0


def grade(request: GradingRequest) -> float:
    private_dir: Path = request.references.private_dir
    submission_root: Path = request.submission.root

    # Load gold image from private/result.png
    gold_path = private_dir / "result.png"
    if not gold_path.exists():
        print(f"Gold image not found: {gold_path}")
        return 0.0
    gold_img = Image.open(gold_path).convert("RGB")

    # Load submission directly as PNG
    pred_path = submission_root
    if not pred_path.exists():
        print(f"Submission file not found: {pred_path}")
        return 0.0
    pred_img = Image.open(pred_path).convert("RGB")

    return judge_image(pred_img, gold_img, threshold=THRESHOLD)
