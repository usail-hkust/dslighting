from pathlib import Path
import shutil

GOLD_FILES = ['sample_cleaned_cycle.csv', 'sample_cleaned_run.csv', 'sample_cleaned_walk.csv']

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and not f.name.startswith("_"):
            shutil.copy2(f, public / f.name)

    gold_dir = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-wrangling-029"
    for gold_file in GOLD_FILES:
        gold = gold_dir / gold_file
        if gold.exists():
            header = gold.read_text().splitlines()[0]
            (public / gold_file).write_text(header + "\n")
            shutil.copy2(gold, private / gold_file)
