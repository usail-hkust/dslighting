"""Grading function for ScienceBench task 53 (mountainlion3 reclassification)."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

try:
    from rasterio.io import MemoryFile
except ImportError as exc:
    raise RuntimeError("Task 53 grading requires the 'rasterio' package.") from exc

EXPECTED_FILES: Dict[str, float] = {
    "landCover_reclassified.tif": 0.70,
    "protected_status_reclassified.tif": 0.70,
}


def _load_raster_from_base64(blob: str) -> np.ndarray:
    if not isinstance(blob, str) or not blob.strip():
        raise ValueError("Empty image_base64 value encountered.")

    data = base64.b64decode(blob)
    with MemoryFile(data) as mem:
        with mem.open() as dataset:
            return dataset.read(1)


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    if submission_path.is_file():
        raise ValueError("Submission should be a directory for this task.")

    answers_df = pd.read_csv(answers_path)

    required_columns = {"file_name", "image_base64"}
    if not required_columns.issubset(answers_df.columns):
        raise ValueError(f"Answers must contain columns: {required_columns}")

    ratios: Dict[str, float] = {}
    for _, row in answers_df.iterrows():
        file_name = row.get("file_name")
        if file_name not in EXPECTED_FILES:
            continue

        gold_blob = row.get("image_base64", "")
        if not gold_blob or pd.isna(gold_blob):
            print(f"Empty gold image for {file_name}")
            continue

        submission_file = submission_path / file_name
        if not submission_file.exists():
            print(f"Submission file not found: {submission_file}")
            continue

        # Read submission file as base64
        with open(submission_file, 'rb') as f:
            pred_blob = base64.b64encode(f.read()).decode('utf-8')

        try:
            pred = _load_raster_from_base64(pred_blob)
            gold = _load_raster_from_base64(gold_blob)
        except Exception as e:
            print(f"Error loading raster: {e}")
            continue

        if pred.shape != gold.shape:
            ratio = 0.0
        else:
            ratio = float(np.mean(pred == gold))
        ratios[file_name] = ratio
        print(f"[grade] {file_name} match ratio={ratio:.4f}")

    missing = sorted(set(EXPECTED_FILES) - ratios.keys())
    if missing:
        print(f"Missing expected raster(s): {', '.join(missing)}")
        return 0.0

    for file_name, threshold in EXPECTED_FILES.items():
        ratio = ratios[file_name]
        if ratio <= threshold:
            print(f"Match ratio for '{file_name}' ({ratio:.4f}) did not exceed {threshold:.2f}.")
            return 0.0

    return 1.0
