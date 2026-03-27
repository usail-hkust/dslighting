"""Grading function for ScienceBench Task 41 (MD KNN models)."""

import numpy as np
from sklearn.metrics import f1_score

from dslighting.benchmark.grading.helpers import (
    read_reference_child_csv,
    read_submission_child_csv,
)

OUTPUT_FILES = {
    "all": "MD_all_KNN.csv",
    "MCNC": "MD_MCNC_KNN.csv",
    "MCLCNC": "MD_MCLCNC_KNN.csv",
}
F1_THRESHOLD = 0.73


def grade(request) -> float:
    gold_df = read_reference_child_csv(request, "answer.csv")

    if gold_df is None or gold_df.empty:
        print("Answer data is empty.")
        return 0.0
    if "label" not in gold_df.columns:
        print("Answers missing 'label' column.")
        return 0.0

    gold_labels = gold_df["label"].reset_index(drop=True)

    f1_scores = []
    for split, filename in OUTPUT_FILES.items():
        pred_df = read_submission_child_csv(request, filename)
        required_cols = {"label"}
        if not required_cols.issubset(pred_df.columns):
            print(f"[{split}] missing label column")
            return 0.0

        if len(pred_df) != len(gold_labels):
            print(f"[{split}] row count mismatch: {len(pred_df)} vs {len(gold_labels)}")
            return 0.0

        f1 = f1_score(gold_labels.values, pred_df["label"].values, pos_label="DILI")
        print(f"[{split}] F1 score: {f1}")
        f1_scores.append(f1)

    mean_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0
    print(f"Mean F1: {mean_f1}")
    return 1.0 if mean_f1 >= F1_THRESHOLD else 0.0
