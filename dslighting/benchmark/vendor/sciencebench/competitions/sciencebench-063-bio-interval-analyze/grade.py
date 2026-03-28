"""
Grading for sciencebench-063-bio-interval-analyze (bio-interval-analyze) – multi-image visualization task.

All expected images must independently pass the VLM / pixel judge (threshold 60.0).
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image

from dslighting.benchmark.grading import judge_image
from dslighting.benchmark.grading.models import GradingRequest

EXPECTED_FILES = ('bio_ecg_plot.png', 'bio_rsp_plot.png')
GOLD_MAPPING = {
    "bio_ecg_plot.png": "bio_ecg_plot_gold.png",
    "bio_rsp_plot.png": "bio_rsp_plot_gold.png",
}
THRESHOLD = 60.0

def grade(request: GradingRequest) -> float:
    private_dir: Path = request.references.private_dir
    missing = [filename for filename in EXPECTED_FILES if not (private_dir / GOLD_MAPPING[filename]).exists()]
    if missing:
        print(f"Missing gold images: {', '.join(GOLD_MAPPING[name] for name in missing)}")
        return 0.0

    submission_root: Path = request.submission.root

    for filename in EXPECTED_FILES:
        gold_img = Image.open(private_dir / GOLD_MAPPING[filename]).convert("RGB")
        pred_path = submission_root / filename
        if not pred_path.exists():
            print(f"Submission file not found: {pred_path}")
            return 0.0
        pred_img = Image.open(pred_path).convert("RGB")
        result = judge_image(pred_img, gold_img, threshold=THRESHOLD)
        if result < 1.0:
            print(f"Image {filename!r} did not pass threshold {THRESHOLD}")
            return 0.0

    return 1.0
