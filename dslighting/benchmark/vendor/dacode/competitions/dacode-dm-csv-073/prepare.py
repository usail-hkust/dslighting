from pathlib import Path
import shutil
import json

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-073"
SKIP_FROM_PUBLIC = {"README.md", "tips.md"}


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and f.name not in SKIP_FROM_PUBLIC:
            shutil.copy2(f, public / f.name)

    gold_src = GOLD_DIR / "result.json"
    if gold_src.exists():
        shutil.copy2(gold_src, private / "answer.json")

    gold_data = None
    answer_json = private / "answer.json"
    if answer_json.exists():
        with open(answer_json, encoding="utf-8") as f:
            gold_data = json.load(f)

    if gold_data:
        sample_data = {k: [] for k in gold_data.keys()}
        with open(public / "sample_submission.json", "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2)