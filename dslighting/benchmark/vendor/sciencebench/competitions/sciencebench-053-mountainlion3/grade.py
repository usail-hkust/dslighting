"""Grading function for ScienceBench task 53 (mountainlion3 reclassification)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np

from dslighting.benchmark.grading.models import GradingRequest

try:
    import rasterio
except ImportError as exc:
    raise RuntimeError("Task 53 grading requires the 'rasterio' package.") from exc

EXPECTED_FILES: Dict[str, float] = {
    "landCover_reclassified.tif": 0.70,
    "protected_status_reclassified.tif": 0.70,
}
GOLD_MAPPING = {
    "landCover_reclassified.tif": "landCover_reclassified_gold.tif",
    "protected_status_reclassified.tif": "protected_status_reclassified_gold.tif",
}


def _read_raster(path: Path) -> np.ndarray:
    with rasterio.open(path) as dataset:
        return dataset.read(1)


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    if submission_path.is_file():
        raise ValueError("Submission should be a directory for this task.")

    private_dir = request.references.private_dir
    ratios: Dict[str, float] = {}
    for file_name, threshold in EXPECTED_FILES.items():
        gold_path = private_dir / GOLD_MAPPING[file_name]
        if not gold_path.exists():
            print(f"Gold raster not found: {gold_path}")
            return 0.0

        submission_file = submission_path / file_name
        if not submission_file.exists():
            print(f"Submission file not found: {submission_file}")
            return 0.0

        try:
            pred = _read_raster(submission_file)
            gold = _read_raster(gold_path)
        except Exception as exc:
            print(f"Error loading raster {file_name}: {exc}")
            return 0.0

        ratio = 0.0 if pred.shape != gold.shape else float(np.mean(pred == gold))
        ratios[file_name] = ratio
        print(f"[grade] {file_name} match ratio={ratio:.4f}")
        if ratio <= threshold:
            print(f"Match ratio for '{file_name}' ({ratio:.4f}) did not exceed {threshold:.2f}.")
            return 0.0

    return 1.0
