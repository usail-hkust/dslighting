"""
Grading for sciencebench-043-eog-analyze (eog-analyze) – visualization task.

Evaluation strategy:
  1. VLM judge (JUDGE_IMAGE_MODEL) with rubric-informed prompt.
  2. Pixel-similarity fallback (PSNR + Pearson) if VLM is unavailable.
Threshold: 60.0 / 100.
"""
from __future__ import annotations

import base64
import io
import json

import pandas as pd
from pathlib import Path
from PIL import Image

from dslighting.benchmark.grading import judge_image
from dslighting.benchmark.grading.models import GradingRequest

EXPECTED_FILENAME = 'EOG_analyze_pred.png'
THRESHOLD = 60.0


def _build_rubric_supplement(rubric: dict) -> str:
    """Build a task-specific rubric supplement for the shared image judge."""
    sections = []
    for key in ("modeling_or_analysis_or_visualization", "output_formatting"):
        items = rubric.get(key, [])
        for item in items:
            desc = item.get("description", "")
            if desc:
                sections.append(f"- {desc}")
    return "\n".join(sections) if sections else "Matches the gold reference plot."


def grade(request: GradingRequest) -> float:
    private_dir: Path = request.references.private_dir
    answers_path = private_dir / "answer.csv"
    rubric_path = private_dir / "rubric.json"

    # Load gold image from answer.csv
    answers_df = pd.read_csv(answers_path)
    if "file_name" not in answers_df.columns or "image_base64" not in answers_df.columns:
        raise ValueError("answer.csv must contain columns: file_name, image_base64")

    gold_row = answers_df[answers_df["file_name"] == EXPECTED_FILENAME]
    if gold_row.empty:
        print(f"Gold entry for {EXPECTED_FILENAME!r} not found in answer.csv")
        return 0.0

    gold_b64 = gold_row["image_base64"].iloc[0]
    if not gold_b64 or pd.isna(gold_b64):
        print(f"Gold image base64 is empty for {EXPECTED_FILENAME!r}")
        return 0.0

    gold_img = Image.open(io.BytesIO(base64.b64decode(gold_b64))).convert("RGB")

    # Load submission image
    submission_root: Path = request.submission.root
    # submission.root may point directly to the file or to a directory
    if submission_root.is_file():
        pred_path = submission_root
    else:
        pred_path = submission_root / EXPECTED_FILENAME

    if not pred_path.exists():
        print(f"Submission file not found: {pred_path}")
        return 0.0

    pred_img = Image.open(pred_path).convert("RGB")

    # Build rubric-informed VLM prompt
    rubric_supplement: str | None = None
    if rubric_path.exists():
        try:
            rubric = json.loads(rubric_path.read_text())
            rubric_supplement = _build_rubric_supplement(rubric)
        except Exception as exc:
            print(f"[grade] Could not load rubric ({exc}); using default prompt.")

    return judge_image(pred_img, gold_img, threshold=THRESHOLD, rubric_supplement=rubric_supplement)
