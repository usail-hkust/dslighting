"""Grading for sciencebench-065-plotting-surface-mass – visualization task."""
from __future__ import annotations
from pathlib import Path
from PIL import Image
from dslighting.benchmark.grading import judge_image
from dslighting.benchmark.grading.models import GradingRequest

THRESHOLD = 60.0
PROMPT_ORIGIN = """You are an excellent judge at evaluating visualization plots between a model generated plot and the ground truth. You will be giving scores on how well it matches the ground truth plot.

The generated plot will be given to you as the first figure. If the first figure is blank, that means the code failed to generate a figure.
Another plot will be given to you as the second figure, which is the desired outcome of the user query, meaning it is the ground truth for you to reference.
Please compare the two figures head to head and rate them.Suppose the second figure has a score of 100, rate the first figure on a scale from 0 to 100.
Scoring should be carried out regarding the plot correctness: Compare closely between the generated plot and the ground truth, the more resemblance the generated plot has compared to the ground truth, the higher the score. The score should be proportionate to the resemblance between the two plots.
In some rare occurrence, see if the data points are generated randomly according to the query, if so, the generated plot may not perfectly match the ground truth, but it is correct nonetheless.
Only rate the first figure, the second figure is only for reference.
After scoring from the above aspect, please give a final score. The final score is preceded by the [FINAL SCORE] token. For example [FINAL SCORE]: 40."""

def grade(request: GradingRequest) -> float:
    private_dir: Path = request.references.private_dir
    submission_root: Path = request.submission.root
    gold_path = private_dir / "result.png"
    if not gold_path.exists():
        print(f"Gold image not found: {gold_path}")
        return 0.0
    gold_img = Image.open(gold_path).convert("RGB")
    pred_path = submission_root
    if not pred_path.exists():
        print(f"Submission file not found: {pred_path}")
        return 0.0
    pred_img = Image.open(pred_path).convert("RGB")
    return judge_image(pred_img, gold_img, threshold=THRESHOLD, prompt=PROMPT_ORIGIN)
