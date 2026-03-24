from pathlib import Path
import shutil

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-027"
SKIP_FROM_PUBLIC = {"README.md", "Top_10_Movies.csv", "Top_10_countries.csv"}


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and f.name not in SKIP_FROM_PUBLIC:
            shutil.copy2(f, public / f.name)

    gold_countries = GOLD_DIR / "Top_10_countries.csv"
    gold_movies = GOLD_DIR / "Top_10_Movies.csv"

    if gold_countries.exists():
        shutil.copy2(gold_countries, private / "answer.csv")
        with open(gold_countries, encoding="utf-8") as f:
            header_line = f.readline()
        with open(public / "sample_submission.csv", "w", encoding="utf-8") as f:
            f.write(header_line)