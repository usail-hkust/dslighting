from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare bike-sharing-demand dataset.

    Raw data already contains:
    - train.csv: training data with labels
    - test.csv: test data without labels
    - sampleSubmission.csv: sample submission format
    - test_answer.csv: test labels (private)
    """
    # Read data
    train = pd.read_csv(raw / "train.csv")
    test = pd.read_csv(raw / "test.csv")
    sample_submission = pd.read_csv(raw / "sampleSubmission.csv")
    test_answer = pd.read_csv(raw / "test_answer.csv")

    # Public files (visible to agents)
    train.to_csv(public / "train.csv", index=False)
    test.to_csv(public / "test.csv", index=False)
    sample_submission.to_csv(public / "sampleSubmission.csv", index=False)

    # Private files (for grading)
    test_answer.to_csv(private / "test.csv", index=False)

    # Validation checks
    assert len(test_answer) == len(test), \
        f"Test answer ({len(test_answer)}) and test ({len(test)}) must have same length"
    assert len(sample_submission) == len(test), \
        f"Sample submission ({len(sample_submission)}) and test ({len(test)}) must have same length"
    assert "datetime" in test_answer.columns, "Test answer must have 'datetime' column"
    assert "count" in test_answer.columns, "Test answer must have 'count' column"
    assert "datetime" in sample_submission.columns, "Sample submission must have 'datetime' column"
    assert "count" in sample_submission.columns, "Sample submission must have 'count' column"
