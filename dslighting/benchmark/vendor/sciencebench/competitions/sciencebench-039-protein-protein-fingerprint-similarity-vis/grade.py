
"""Grading function for ScienceBench task 39."""

import numpy as np
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


def _grade_visual_similarity(submission_path: Path, gold_path: Path, threshold_score: float) -> float:
    """Grade by comparing a submitted PNG against the gold PNG."""
    gold_img = Image.open(gold_path)

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
    gold_path = request.references.private_dir / "result.png"
    if not gold_path.exists():
        print(f"Gold image not found: {gold_path}")
        return 0.0

    return _grade_visual_similarity(submission_path, gold_path, THRESHOLD)
