from pathlib import Path
import shutil

SUBMISSION_FILENAME = "sample_submission.csv"

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy source files to public (excluding _* files)
    for f in raw.iterdir():
        if f.is_file() and not f.name.startswith("_"):
            shutil.copy2(f, public / f.name)

    # Gold is in gold/ directory - use gold header for template
    gold = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-wrangling-011" / SUBMISSION_FILENAME
    if gold.exists():
        header = gold.read_text().splitlines()[0]
        (public / SUBMISSION_FILENAME).write_text(header + "\n")
        shutil.copy2(gold, private / "answer.csv")
