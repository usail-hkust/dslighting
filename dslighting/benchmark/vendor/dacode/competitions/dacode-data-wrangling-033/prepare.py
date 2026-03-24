from pathlib import Path
import shutil

DB_FILENAME = "travel.sqlite"

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy source DB to public (agent works on this)
    for f in raw.iterdir():
        if f.is_file() and not f.name.startswith("_"):
            shutil.copy2(f, public / f.name)

    # Copy gold DB to private
    gold = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-wrangling-033" / DB_FILENAME
    shutil.copy2(gold, private / DB_FILENAME)
