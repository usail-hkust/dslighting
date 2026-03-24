from pathlib import Path
import shutil, pandas as pd

GOLD_FILES = ['kruskal_wallis_results.csv']

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    gold_set = set(GOLD_FILES)
    for f in raw.iterdir():
        if f.name not in gold_set:
            shutil.copy2(f, public / f.name)
    dfs = [pd.read_csv(raw / g) for g in GOLD_FILES if (raw / g).exists()]
    if dfs:
        pd.concat(dfs, axis=1).to_csv(private / "answer.csv", index=False)
    if dfs:
        dfs[0].head(0).to_csv(public / "sample_submission.csv", index=False)
    else:
        (public / "sample_submission.csv").write_text("result\n")
