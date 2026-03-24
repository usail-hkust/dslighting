from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy answer from gold directory
    gold_answer = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-competition-018" / "submission.csv"
    if gold_answer.exists():
        gold_df = pd.read_csv(gold_answer)
        gold_df.to_csv(private / 'answer.csv', index=False)

        # Create sample_submission.csv with placeholder values
        sample_df = gold_df.copy()
        pred_cols = [c for c in gold_df.columns if c.lower() != 'id']
        for col in pred_cols:
            if pd.api.types.is_numeric_dtype(gold_df[col]):
                sample_df[col] = 0.5
            else:
                sample_df[col] = gold_df[col].iloc[0]
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy training and test data
    for fname in ['train_essays.csv', 'test_essays.csv']:
        f = raw / fname
        if f.exists():
            shutil.copy2(f, public / fname)

    # Copy README
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
