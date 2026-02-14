from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the DABench task 528 dataset.

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
        'id': [528],
        'answer': ['@placeholder[0.00]']  # Placeholder answer
    })
    sample_submission_file = public / "sample_submission.csv"
    sample_submission.to_csv(sample_submission_file, index=False)
    print(f"Created sample submission: {sample_submission_file}")

    # Create answer file (ground truth)
    answer = pd.DataFrame({
        'id': [528],
        'answer': ['@outlier_ids[904, 916, 940, 945, 951, 956, 961, 966, 967, 973, 988, 1006, 1010, 1033, 1034, 1042, 1048, 1071, 1073, 1076, 1080, 1088, 1094, 1104, 1109, 1110, 1126, 1128, 1131, 1134, 1144, 1162, 1164, 1179, 1185, 1198, 1200, 1206, 1208, 1216, 1219, 1234, 1235, 1244, 1252, 1257, 1263, 1266, 1267, 1282, 1289, 1292, 1299, 1303, 1306] @outlier_count[55]']
    })
    answer_file = private / "answer.csv"
    answer.to_csv(answer_file, index=False)
    print(f"Created answer file: {answer_file}")

    # Verify
    assert train_file.exists(), "Training file not created"
    assert sample_submission_file.exists(), "Sample submission not created"
    assert answer_file.exists(), "Answer file not created"

    print(f"✓ DABench task 528 prepared successfully")
