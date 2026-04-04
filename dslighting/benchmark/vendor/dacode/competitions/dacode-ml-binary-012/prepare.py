from pathlib import Path
import shutil, pandas as pd

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-binary-012"
TRAIN_COLUMNS = ["emotion", "id", "date", "query", "user", "text"]
TEST_COLUMNS = ["id", "date", "query", "user", "text"]

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    gold_file = GOLD_DIR / "sentiment.csv"
    answer_df = None
    if gold_file.exists():
        shutil.copy2(gold_file, private / "answer.csv")
        answer_df = pd.read_csv(gold_file)

    # Copy and normalize test data
    test_file = raw / 'test.csv'
    if test_file.exists():
        test_df = pd.read_csv(test_file, header=None, names=TEST_COLUMNS)
        test_df.to_csv(public / 'test.csv', index=False)
        if answer_df is not None and len(test_df) != len(answer_df):
            raise ValueError(
                f"ml-binary-012 row mismatch: test.csv has {len(test_df)} rows but "
                f"gold answer has {len(answer_df)} rows."
            )

    if answer_df is not None:
        first_vals = answer_df.iloc[0].values
        sample_df = pd.DataFrame([first_vals] * len(answer_df), columns=answer_df.columns)
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy and normalize train data
    train_file = raw / 'training.1600000.processed.noemoticon.csv'
    if train_file.exists():
        train_df = pd.read_csv(
            train_file,
            header=None,
            names=TRAIN_COLUMNS,
            encoding="latin-1",
        )
        train_df.to_csv(public / 'train.csv', index=False)

    # Copy README
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
