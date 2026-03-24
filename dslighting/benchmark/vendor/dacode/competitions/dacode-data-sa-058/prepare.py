from pathlib import Path
import shutil, json

GOLD_FILES = ['result.json']

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    gold_set = set(GOLD_FILES)
    for f in raw.iterdir():
        if f.name not in gold_set:
            shutil.copy2(f, public / f.name)

    # Handle JSON answer from gold directory
    gold_dir = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-sa-058"
    for gold_file in GOLD_FILES:
        gold_path = gold_dir / gold_file
        if gold_path.exists():
            shutil.copy2(gold_path, private / "answer.json")
            (public / "sample_submission.json").write_text("{}\n")
