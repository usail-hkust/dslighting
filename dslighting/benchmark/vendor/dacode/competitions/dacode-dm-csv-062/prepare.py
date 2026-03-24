from pathlib import Path
import shutil

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-062"
SKIP_FROM_PUBLIC = {"README.md", "result.csv"}


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and f.name not in SKIP_FROM_PUBLIC:
            shutil.copy2(f, public / f.name)

    gold_src = GOLD_DIR / "result.csv"
    if gold_src.exists():
        shutil.copy2(gold_src, private / "answer.csv")

    answer_csv = private / "answer.csv"
    if answer_csv.exists():
        with open(answer_csv, encoding="utf-8") as f:
            header_line = f.readline()
        with open(public / "sample_submission.csv", "w", encoding="utf-8") as f:
            f.write(header_line)
