from pathlib import Path
import shutil, pandas as pd

GOLD_FILES = ['before_covariance.csv', 'during_covariance.csv', 'after_covariance.csv']

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    gold_set = set(GOLD_FILES)
    for f in raw.iterdir():
        if f.name not in gold_set:
            shutil.copy2(f, public / f.name)
    # Copy gold files separately to private/ (not merged)
    for g in GOLD_FILES:
        if (raw / g).exists():
            shutil.copy2(raw / g, private / g)
            # Create sample file with "sample_" prefix
            df = pd.read_csv(raw / g)
            df.head(0).to_csv(public / f"sample_{g}", index=False)
