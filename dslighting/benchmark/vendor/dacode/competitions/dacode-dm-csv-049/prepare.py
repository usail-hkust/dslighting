import json
from pathlib import Path
import shutil
import pandas as pd

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-049"
SKIP_FROM_PUBLIC = {"README.md"}


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and f.name not in SKIP_FROM_PUBLIC:
            shutil.copy2(f, public / f.name)

    gold_src = GOLD_DIR / "result.json"
    if gold_src.exists():
        with open(gold_src, 'r') as f:
            data = json.load(f)

        rows = []
        for key, values in data.items():
            if isinstance(values, list) and len(values) > 0:
                val = values[0]
            else:
                val = values
            rows.append({key: val})

        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(private / "answer.csv", index=False)

            with open(private / "answer.csv", 'r') as f:
                header_line = f.readline()
            with open(public / "sample_submission.csv", "w") as f:
                f.write(header_line)