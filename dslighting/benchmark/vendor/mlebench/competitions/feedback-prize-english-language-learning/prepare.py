from pathlib import Path
import pandas as pd


TARGET_COLUMNS = ['cohesion', 'syntax', 'vocabulary', 'phraseology', 'grammar', 'conventions']


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare feedback-prize-english-language-learning dataset.

    Raw data contains:
    - train.csv: training data with text and scores
    - test.csv: test data with text only
    - sample_submission.csv: sample submission format
    - test_answer.csv: test labels (private)
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
    assert "text_id" in test_answer.columns, "Test answer must have 'text_id' column"
    assert "text_id" in sample_submission.columns, "Sample submission must have 'text_id' column"
    for col in TARGET_COLUMNS:
        assert col in test_answer.columns, f"Test answer must have '{col}' column"
        assert col in sample_submission.columns, f"Sample submission must have '{col}' column"
