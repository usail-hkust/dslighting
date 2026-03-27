"""
Grading function for ScienceBench task 5 (DKPES model development).

Mirrors the original ScienceAgentBench evaluation:
1. Verify the `index` column matches between submission and gold labels.
2. Binarize gold labels: Signal-inhibition >= 0.6 -> 1, else 0
3. Compute accuracy_score and require >= 0.91 to pass.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from dslighting.benchmark.grading.models import GradingRequest


THRESHOLD = 0.91
BINARIZE_THRESHOLD = 0.6


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answers_path)

    # Check index ordering
    if list(submission["index"]) != list(answers["index"]):
        print("Index mismatch between submission and gold.")
        return 0.0

    # Binarize gold labels
    gold_labels = np.where(answers["Signal-inhibition"].values >= BINARIZE_THRESHOLD, 1, 0)

    # Compute accuracy
    try:
        metric = accuracy_score(gold_labels, submission["Signal-inhibition"].values)
    except ValueError as exc:
        print(f"Failed to compute accuracy: {exc}")
        return 0.0

    print(f"Accuracy: {metric:.4f} (threshold: {THRESHOLD})")
    return 1.0 if metric >= THRESHOLD else 0.0
