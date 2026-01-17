from pathlib import Path

import pandas as pd

from mlebench.utils import read_csv


def prepare(raw: Path, public: Path, private: Path) -> None:
    """Prepare Reverse Game of Life tables for MLE-Bench."""
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    train = read_csv(raw / "train.csv")
    test = read_csv(raw / "test.csv")
    answers = read_csv(raw / "test_answer.csv")

    sample_path = raw / "sample_submission.csv"
    if sample_path.exists():
        sample_submission = read_csv(sample_path)
    else:
        start_cols = [col for col in answers.columns if col.startswith("start_")]
        sample_submission = answers[["id", *start_cols]].copy()
        sample_submission[start_cols] = 0

    merged_private = test.merge(answers, on="id", how="left", validate="one_to_one")
    start_cols = [col for col in answers.columns if col.startswith("start_")]
    if merged_private[start_cols].isna().any().any():
        missing_ids = merged_private.loc[merged_private[start_cols].isna().any(axis=1), "id"].tolist()
        raise ValueError(f"Missing start cells for ids: {missing_ids[:5]}")

    train.to_csv(public / "train.csv", index=False)
    test.to_csv(public / "test.csv", index=False)
    sample_submission.to_csv(public / "sample_submission.csv", index=False)

    merged_private.to_csv(private / "test.csv", index=False)
    answers.to_csv(private / "gold_submission.csv", index=False)

    assert len(test) == len(answers) == len(merged_private), "Public test and answers row counts differ."
    assert sample_submission.columns.tolist()[0] == "id", "Sample submission must start with 'id'."
    for col in start_cols:
        assert col in sample_submission.columns, f"Sample submission missing column {col}."
