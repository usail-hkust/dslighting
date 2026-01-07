from pathlib import Path

import pandas as pd

from mlebench.utils import read_csv


def prepare(raw: Path, public: Path, private: Path) -> None:
    """Materialize Santander Customer Satisfaction CSV splits."""
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    train = read_csv(raw / "train.csv")
    test_public = read_csv(raw / "test.csv")
    answers = read_csv(raw / "test_answer.csv")

    if (raw / "sample_submission.csv").exists():
        sample_submission = read_csv(raw / "sample_submission.csv")
    else:
        sample_submission = answers.copy()
        sample_submission["TARGET"] = 0.0

    merged_private = test_public.merge(answers, on="ID", how="left", validate="one_to_one")
    if merged_private["TARGET"].isna().any():
        missing_ids = merged_private.loc[merged_private["TARGET"].isna(), "ID"].tolist()[:5]
        raise ValueError(f"Missing TARGET labels for IDs (showing up to 5): {missing_ids}")

    train.to_csv(public / "train.csv", index=False)
    test_public.to_csv(public / "test.csv", index=False)
    sample_submission.to_csv(public / "sample_submission.csv", index=False)

    merged_private.to_csv(private / "test.csv", index=False)
    answers.to_csv(private / "gold_submission.csv", index=False)

    assert len(test_public) == len(answers) == len(
        merged_private
    ), "Test features, answers, and private test must have the same length."
    assert set(train.columns) - {"TARGET"} == set(
        test_public.columns
    ), "Train and public test feature columns should match aside from TARGET."
    assert sample_submission.columns.tolist() == ["ID", "TARGET"], "Sample submission must be ID,TARGET."
