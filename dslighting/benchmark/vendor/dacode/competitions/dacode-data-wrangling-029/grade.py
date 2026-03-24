from __future__ import annotations

import numpy as np
import pandas as pd

from dslighting.benchmark.grading.models import GradingRequest

FLOAT_TOLERANCE = 1e-2
IGNORE_ORDER = False
GOLD_FILES = ("sample_cleaned_cycle.csv", "sample_cleaned_run.csv", "sample_cleaned_walk.csv")


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def _compare_frame(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    submission = _normalize(submission)
    answers = _normalize(answers)

    if list(submission.columns) != list(answers.columns) or len(submission) != len(answers):
        return 0.0

    if IGNORE_ORDER:
        submission = submission.sort_values(list(submission.columns)).reset_index(drop=True)
        answers = answers.sort_values(list(answers.columns)).reset_index(drop=True)

    file_scores = []
    for col in answers.columns:
        sub_num = pd.to_numeric(submission[col], errors="coerce")
        ans_num = pd.to_numeric(answers[col], errors="coerce")
        if ans_num.notna().mean() > 0.5:
            match = np.isclose(sub_num, ans_num, rtol=FLOAT_TOLERANCE, equal_nan=True)
        else:
            match = submission[col].fillna("").astype(str).str.strip() == answers[col].fillna("").astype(str).str.strip()
        file_scores.append(float(match.mean()))
    return float(np.mean(file_scores)) if file_scores else 0.0


def grade(request: GradingRequest) -> float:
    submission_root = request.submission.root
    answers_dir = request.references.private_dir

    scores = []
    for gold_file in GOLD_FILES:
        sub_path = submission_root / gold_file
        ans_path = answers_dir / gold_file
        if not sub_path.exists() or not ans_path.exists():
            scores.append(0.0)
            continue
        try:
            submission = pd.read_csv(sub_path, dtype=str)
            answers = pd.read_csv(ans_path, dtype=str)
        except Exception:
            scores.append(0.0)
            continue
        scores.append(_compare_frame(submission, answers))

    return float(np.mean(scores)) if scores else 0.0
