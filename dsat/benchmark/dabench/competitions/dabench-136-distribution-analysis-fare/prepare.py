from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the DABench task 136 dataset.

    Args:
        raw: Path to raw data directory (should contain titanic.csv)
        public: Path to public directory (for participants)
        private: Path to private directory (for grading)
    """
    # Load the data
    data_file = raw / "titanic.csv"
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    df = pd.read_csv(data_file)

    # Save the full dataset to public directory
    train_file = public / "train.csv"
    df.to_csv(train_file, index=False)
    print(f"Saved training data to {train_file} ({len(df)} rows)")

    # Create sample submission file
    sample_submission = pd.DataFrame({
        'id': [136],
        'answer': ['@placeholder[0.00]']  # Placeholder answer
    })
    sample_submission_file = public / "sample_submission.csv"
    sample_submission.to_csv(sample_submission_file, index=False)
    print(f"Created sample submission: {sample_submission_file}")

    # Create answer file (ground truth)
    answer = pd.DataFrame({
        'id': [136],
        'answer': ['@p_value_class_1[0.0000] @p_value_class_3[0.0000] @p_value_class_2[0.0000]']
    })
    answer_file = private / "answer.csv"
    answer.to_csv(answer_file, index=False)
    print(f"Created answer file: {answer_file}")

    # Verify
    assert train_file.exists(), "Training file not created"
    assert sample_submission_file.exists(), "Sample submission not created"
    assert answer_file.exists(), "Answer file not created"

    print(f"✓ DABench task 136 prepared successfully")
