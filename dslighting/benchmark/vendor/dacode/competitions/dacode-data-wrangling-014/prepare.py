from pathlib import Path
import shutil

DB_FILENAME = "cleaned_parking_violation.db"

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and f.name != DB_FILENAME and not f.name.startswith("_"):
            shutil.copy2(f, public / f.name)

    gold = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-wrangling-014" / DB_FILENAME
    if gold.exists():
        shutil.copy2(gold, private / DB_FILENAME)
