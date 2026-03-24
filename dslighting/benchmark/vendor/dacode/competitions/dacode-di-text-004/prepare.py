from pathlib import Path
import shutil, pandas as pd

GOLD_FILES = ['result.json']
SKIP_FILES = {'README.md'}

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    gold_set = set(GOLD_FILES)
    skip_set = set(SKIP_FILES)

    for f in raw.iterdir():
        if f.name not in gold_set and f.name not in skip_set:
            shutil.copy2(f, public / f.name)

    for g in GOLD_FILES:
        if (raw / g).exists():
            import json
            with open(raw / g) as f:
                data = json.load(f)

            def flatten(d, parent_key=''):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}_{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten(v, new_key).items())
                    elif isinstance(v, list):
                        if len(v) == 1:
                            items.append((new_key, v[0]))
                        else:
                            items.append((new_key, str(v)))
                    else:
                        items.append((new_key, v))
                return dict(items)

            flat = flatten(data)
            df = pd.DataFrame([flat])
            df.to_csv(private / "answer.csv", index=False)

            # sample_submission.csv: 和 answer.csv 格式一样，但值是 placeholder
            sample_df = pd.DataFrame(columns=df.columns)
            for col in sample_df.columns:
                sample_df[col] = ['placeholder']
            sample_df.to_csv(public / "sample_submission.csv", index=False)
