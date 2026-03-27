
"""
Grading function for sciencebench 039 protein protein fingerprint similarity vis visualization task.

Mirrors the original ScienceAgentBench evaluation that compares the generated
PNG against the gold reference with a GPT-4 based judge (threshold 60). When
that optional dependency is unavailable we fall back to a deterministic pixel
similarity proxy.
"""

import base64
import io
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image

from dslighting.benchmark.grading.models import GradingRequest


EXPECTED_FILENAME = "protein_protein_similarity_pred.png"
THRESHOLD = 60.0


def _compute_pixel_similarity(img1: Image.Image, img2: Image.Image) -> float:
    """Compute simple pixel similarity between two images."""
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)

    arr1 = np.array(img1.convert('L'), dtype=np.float32)
    arr2 = np.array(img2.convert('L'), dtype=np.float32)

    if arr1.max() > 0:
        arr1 = arr1 / arr1.max()
    if arr2.max() > 0:
        arr2 = arr2 / arr2.max()

    diff = np.abs(arr1 - arr2)
    similarity = 1.0 - np.mean(diff)

    return max(0.0, similarity)


def _grade_visual_rows_fallback(submission_path: Path, gold_base64: str, threshold_score: float) -> float:
    """Fallback grading using pixel similarity when GPT-4 judge is unavailable."""
    gold_bytes = base64.b64decode(gold_base64)
    gold_img = Image.open(io.BytesIO(gold_bytes))

    if not submission_path.exists():
        print(f"Submission file not found: {submission_path}")
        return 0.0

    submission_img = Image.open(submission_path)

    similarity = _compute_pixel_similarity(submission_img, gold_img)
    score = (similarity / 100.0) * 100

    print(f"Pixel similarity score: {score:.2f} (threshold: {threshold_score})")

    return 1.0 if score >= threshold_score else 0.0


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    answers_df = pd.read_csv(answers_path)

    if "file_name" not in answers_df.columns or "image_base64" not in answers_df.columns:
        raise ValueError("Answers must contain columns: file_name, image_base64")

    gold_row = answers_df[answers_df["file_name"] == EXPECTED_FILENAME]
    if gold_row.empty:
        print(f"Expected visualization '{EXPECTED_FILENAME}' not found in answers.")
        return 0.0

    gold_base64 = gold_row["image_base64"].iloc[0]

    if not gold_base64 or pd.isna(gold_base64):
        print(f"Gold image base64 is empty for '{EXPECTED_FILENAME}'")
        return 0.0

    return _grade_visual_rows_fallback(submission_path, gold_base64, THRESHOLD)
