from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the DABench task 527 dataset.

    Args:
        raw: Path to raw data directory (should contain titanic_test.csv)
        public: Path to public directory (for participants)
        private: Path to private directory (for grading)
    """
    # Load the data
    data_file = raw / "titanic_test.csv"
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    df = pd.read_csv(data_file)

    # Save the full dataset to public directory
    train_file = public / "train.csv"
    df.to_csv(train_file, index=False)
    print(f"Saved training data to {train_file} ({len(df)} rows)")

    # Create sample submission file
    sample_submission = pd.DataFrame({
        'id': [527],
        'answer': ['@placeholder[0.00]']  # Placeholder answer
    })
    sample_submission_file = public / "sample_submission.csv"
    sample_submission.to_csv(sample_submission_file, index=False)
    print(f"Created sample submission: {sample_submission_file}")

    # Create answer file (ground truth)
    answer = pd.DataFrame({
        'id': [527],
        'answer': ['@average_age_male_class2[30.94] @average_age_female_class3[23.07] @average_age_female_class1[41.33] @average_age_female_class2[24.38] @average_age_male_class1[40.52] @average_age_male_class3[24.53]']
    })
    answer_file = private / "answer.csv"
    answer.to_csv(answer_file, index=False)
    print(f"Created answer file: {answer_file}")

    # Verify
    assert train_file.exists(), "Training file not created"
    assert sample_submission_file.exists(), "Sample submission not created"
    assert answer_file.exists(), "Answer file not created"

    print(f"✓ DABench task 527 prepared successfully")
