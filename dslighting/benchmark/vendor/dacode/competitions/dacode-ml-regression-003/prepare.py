from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    gold_dir = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-regression-003"
    gold_file = gold_dir / 'submission.csv'
    if gold_file.exists():
        shutil.copy2(gold_file, private / 'answer.csv')
        df = pd.read_csv(gold_file)
        first_vals = df.iloc[0].values
        placeholder_df = pd.DataFrame([first_vals] * len(df), columns=df.columns)
        placeholder_df.to_csv(public / 'sample_submission.csv', index=False)

    if (raw / 'test.csv').exists():
        shutil.copy2(raw / 'test.csv', public / 'test.csv')

    for train_name in ['train.csv', 'other_names.csv']:
        if (raw / train_name).exists():
            shutil.copy2(raw / train_name, public / 'train.csv')
            break

    if (raw / 'README.md').exists():
        shutil.copy2(raw / 'README.md', public / 'README.md')
