import json
from pathlib import Path
import shutil

SKIP_FROM_PUBLIC = {"README.md", "result.json", "result.csv"}


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and f.name not in SKIP_FROM_PUBLIC:
            shutil.copy2(f, public / f.name)

    raw_result = raw / "result.json"
    if raw_result.exists():
        shutil.copy2(raw_result, private / "answer.json")

        with open(raw_result, "r", encoding="utf-8") as f:
            answer_data = json.load(f)
        sample_data = {key: [] for key in answer_data.keys()}
        with open(public / "sample_submission.json", "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2)
