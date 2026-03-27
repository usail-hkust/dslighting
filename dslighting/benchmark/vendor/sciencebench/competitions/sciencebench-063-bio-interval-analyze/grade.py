"""
Grading for sciencebench-063-bio-interval-analyze (bio-interval-analyze) – multi-image visualization task.

All expected images must independently pass the VLM / pixel judge (threshold 60.0).
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

EXPECTED_FILES = ('bio_ecg_plot.png', 'bio_rsp_plot.png')
THRESHOLD = 60.0


def _build_rubric_supplement(rubric: dict) -> str:
    sections = []
    for key in ("modeling_or_analysis_or_visualization", "output_formatting"):
        for item in rubric.get(key, []):
            desc = item.get("description", "")
            if desc:
                sections.append(f"- {desc}")
    return "\n".join(sections) if sections else "Matches the gold reference plot."


def grade(request: GradingRequest) -> float:
    private_dir: Path = request.references.private_dir
    answers_path = private_dir / "answer.csv"
    rubric_path = private_dir / "rubric.json"

    answers_df = pd.read_csv(answers_path)
    if "file_name" not in answers_df.columns or "image_base64" not in answers_df.columns:
        raise ValueError("answer.csv must contain columns: file_name, image_base64")

    gold_images: dict[str, str] = {
        row["file_name"]: row["image_base64"]
        for _, row in answers_df.iterrows()
        if row.get("file_name") in EXPECTED_FILES and not pd.isna(row.get("image_base64", ""))
    }

    missing = [f for f in EXPECTED_FILES if f not in gold_images]
    if missing:
        print(f"Missing gold images: {', '.join(missing)}")
        return 0.0

    rubric_supplement: str | None = None
    if rubric_path.exists():
        try:
            rubric = json.loads(rubric_path.read_text())
            rubric_supplement = _build_rubric_supplement(rubric)
        except Exception as exc:
            print(f"[grade] Could not load rubric ({exc}); using default prompt.")

    submission_root: Path = request.submission.root

    for filename in EXPECTED_FILES:
        gold_img = Image.open(io.BytesIO(base64.b64decode(gold_images[filename]))).convert("RGB")
        pred_path = submission_root / filename
        if not pred_path.exists():
            print(f"Submission file not found: {pred_path}")
            return 0.0
        pred_img = Image.open(pred_path).convert("RGB")
        result = judge_image(pred_img, gold_img, threshold=THRESHOLD, rubric_supplement=rubric_supplement)
        if result < 1.0:
            print(f"Image {filename!r} did not pass threshold {THRESHOLD}")
            return 0.0

    return 1.0
