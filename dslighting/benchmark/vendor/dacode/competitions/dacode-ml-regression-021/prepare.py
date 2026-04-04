from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    gold_dir = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-regression-021"
    gold_file = gold_dir / 'price.csv'
    if gold_file.exists():
        shutil.copy2(gold_file, private / 'answer.csv')
        df = pd.read_csv(gold_file)
        first_vals = df.iloc[0].values
        placeholder_df = pd.DataFrame([first_vals] * len(df), columns=df.columns)
        placeholder_df.to_csv(public / 'sample_submission.csv', index=False)

    for f in raw.iterdir():
        if f.name == gold_file.name:
            continue
        if f.suffix == '.csv' or f.name == 'README.md':
            shutil.copy2(f, public / f.name)
