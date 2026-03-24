from pathlib import Path
import shutil, pandas as pd
import json

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
                            items.append((new_key, json.dumps(v)))
                    else:
                        items.append((new_key, v))
                return dict(items)

            flat = flatten(data)
            df = pd.DataFrame([flat])
            df.to_csv(private / "answer.csv", index=False)

            # sample_submission.csv: 使用 JSON 数组占位符
            sample_data = {}
            for k, v in data.items():
                if isinstance(v, list):
                    sample_data[k] = [f"place{i+1}" for i in range(len(v))]
                else:
                    sample_data[k] = v

            sample_flat = flatten(sample_data)
            sample_df = pd.DataFrame([sample_flat])
            sample_df.to_csv(public / "sample_submission.csv", index=False)