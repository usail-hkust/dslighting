from pathlib import Path
import pandas as pd


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the house price prediction dataset.

    Splits raw data into:
    - Train set (80%) → public/train.csv
    - Test answers (20%) → private/answer.csv
    - Sample submission → public/sample_submission.csv

    Args:
        raw: Raw data directory (with houses.csv).
        public: Public data directory (visible to participants).
        private: Private data directory (used for scoring).
    """
    # Load raw data
    data_file = raw / "houses.csv"
    if not data_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {data_file}")

    print(f"Loading raw data: {data_file}")
    df = pd.read_csv(data_file)
    print(f"✓ Total rows: {len(df)}")

    # Split train/test (80/20)
    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()

    print(f"✓ Train rows: {len(train_df)}")
    print(f"✓ Test rows: {len(test_df)}")

    # 1. Save train data to public/ (includes price)
    train_file = public / "train.csv"
    train_df.to_csv(train_file, index=False)
    print(f"✓ Train data saved: {train_file}")

    # 2. Create sample submission placeholder
    sample_submission = pd.DataFrame({
        'house_id': test_df['house_id'],
        'predicted_price': [0.0] * len(test_df)  # Placeholder
    })
    sample_file = public / "sample_submission.csv"
    sample_submission.to_csv(sample_file, index=False)
    print(f"✓ Sample submission created: {sample_file}")

    # 3. Save answers to private/ (true test prices)
    answers = test_df[['house_id', 'price']].rename(columns={'price': 'actual_price'})
    answer_file = private / "answer.csv"
    answers.to_csv(answer_file, index=False)
    print(f"✓ Answer file saved: {answer_file}")

    # Validation
    assert train_file.exists(), "Train file not created"
    assert sample_file.exists(), "Sample submission not created"
    assert answer_file.exists(), "Answer file not created"

    print("\n" + "=" * 60)
    print("✅ Data preparation done")
    print("=" * 60)
    print(f"Train: {train_file}")
    print(f"Sample submission: {sample_file}")
    print(f"Answers: {answer_file}")


if __name__ == "__main__":
    # Quick test for the prep script
    import sys
    from pathlib import Path

    # Paths
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / "data" / "custom-house-price-prediction" / "raw"
    public_dir = base_dir / "data" / "custom-house-price-prediction" / "prepared" / "public"
    private_dir = base_dir / "data" / "custom-house-price-prediction" / "prepared" / "private"

    # Create directories
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # Run prep
    try:
        prepare(raw_dir, public_dir, private_dir)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
