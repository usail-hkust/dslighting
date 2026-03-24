from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy validation data as test.csv
    val_file = raw / 'validation.csv'
    if val_file.exists():
        shutil.copy2(val_file, public / 'test.csv')

    # Combine Fake.csv and True.csv as train.csv
    fake_file = raw / 'Fake.csv'
    true_file = raw / 'True.csv'
    if fake_file.exists() and true_file.exists():
        fake_df = pd.read_csv(fake_file)
        true_df = pd.read_csv(true_file)
        train_df = pd.concat([fake_df, true_df], ignore_index=True)
        train_df.to_csv(public / 'train.csv', index=False)

    # Copy answer from gold directory
    gold_answer = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-binary-006" / "result.csv"
    if gold_answer.exists():
        shutil.copy2(gold_answer, private / 'answer.csv')

        # Create sample_submission (copy from gold answer)
        df = pd.read_csv(gold_answer)
        first_vals = df.iloc[0].values
        placeholder_df = pd.DataFrame([first_vals] * len(df), columns=df.columns)
        placeholder_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy README if exists
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
