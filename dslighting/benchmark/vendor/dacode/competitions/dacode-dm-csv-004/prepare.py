from pathlib import Path
import shutil

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-004"
GOLD_FILES = ['allEvents.csv', 'allGames.csv']


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    gold_set = set(GOLD_FILES)
    sample_files = {'sample_allEvents.csv', 'sample_allGames.csv'}

    for f in raw.iterdir():
        if f.is_file() and f.name not in gold_set and f.name not in sample_files:
            shutil.copy2(f, public / f.name)

    for g in GOLD_FILES:
        gold_src = GOLD_DIR / g
        if gold_src.exists():
            shutil.copy2(gold_src, private / g)

    for s in sample_files:
        src = raw / s
        if src.exists():
            dest_name = s.replace('sample_', 'sample_')
            shutil.copy2(src, public / s)
