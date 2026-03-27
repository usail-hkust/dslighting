"""Grading function for ScienceBench Task 40 (MD RF models)."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from dslighting.benchmark.grading.models import GradingRequest

OUTPUT_FILES = {
    "all": Path("MD_all_RF.csv"),
    "MCNC": Path("MD_MCNC_RF.csv"),
    "MCLCNC": Path("MD_MCLCNC_RF.csv"),
}
GOLD_PATH = Path("benchmark/eval_programs/gold_results/MD_gold.csv")
F1_THRESHOLD = 0.73


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Expected submission file missing: {path}")
    return pd.read_csv(path)


def grade(request: GradingRequest) -> float:
    submission_path = request.submission.root
    answers_path = request.references.private_dir / "answer.csv"

    gold_df = _load_csv(answers_path)

    f1_scores = []
    for split, file_path in OUTPUT_FILES.items():
        if submission_path.is_file():
            raise ValueError("Submission should be a directory for this task.")
        pred_df = _load_csv(submission_path / file_path)
        required_cols = {"label"}
        if not required_cols.issubset(pred_df.columns):
            print(f"[{split}] missing label column")
            return 0.0

        if len(pred_df) != len(gold_df):
            print(f"[{split}] row count mismatch: {len(pred_df)} vs {len(gold_df)}")
            return 0.0

        f1 = f1_score(gold_df["label"].values, pred_df["label"].values, pos_label="DILI")
        print(f"[{split}] F1 score: {f1}")
        f1_scores.append(f1)

    mean_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0
    print(f"Mean F1: {mean_f1}")
    return 1.0 if mean_f1 >= F1_THRESHOLD else 0.0
