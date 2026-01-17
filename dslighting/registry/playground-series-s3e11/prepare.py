from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare playground-series-s3e11 dataset.
    """
    # Read data
    train = pd.read_csv(raw / "train.csv")
    test = pd.read_csv(raw / "test.csv")
    sample_submission = pd.read_csv(raw / "sample_submission.csv")
    test_answer = pd.read_csv(raw / "test_answer.csv")

    # Public files (visible to agents)
    train.to_csv(public / "train.csv", index=False)
    test.to_csv(public / "test.csv", index=False)
    sample_submission.to_csv(public / "sample_submission.csv", index=False)

    # Private files (for grading)
    test_answer.to_csv(private / "test.csv", index=False)

    # Validation checks
    assert len(test_answer) == len(sample_submission), \
        f"Test answer ({len(test_answer)}) and sample submission ({len(sample_submission)}) must have same length"
