from pathlib import Path
import shutil
import zipfile

SUBMISSION_FILENAME = "sample_submission.csv"

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and not f.name.startswith("_"):
            if f.suffix == '.zip':
                with zipfile.ZipFile(f, 'r') as z:
                    z.extractall(public)
            else:
                shutil.copy2(f, public / f.name)

    gold = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-wrangling-080" / SUBMISSION_FILENAME
    if gold.exists():
        header = gold.read_text().splitlines()[0]
        (public / SUBMISSION_FILENAME).write_text(header + "\n")
        shutil.copy2(gold, private / "answer.csv")
