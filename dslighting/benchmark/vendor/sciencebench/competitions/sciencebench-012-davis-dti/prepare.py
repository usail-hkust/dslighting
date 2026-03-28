"""Data preparation for ScienceBench Task 12 (DAVIS DTI repurposing)."""

from pathlib import Path
import shutil

DATA_DIR = None  # set inside prepare()
DAVIS_DIR = None  # set inside prepare()
GOLD_TOP5 = [
    "Foscarnet",
    "Boceprevir",
    "Sofosbuvir",
    "Amantadine",
    "Glecaprevir",
]
REMOVED_LAST5 = [
    "Abacavir",
    "Etravirine",
    "Rilpivirine",
    "Imiquimod",
    "Pyrimidine",
]
OUTPUT_FILENAME = "davis_dti_repurposing.txt"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_sample_submission(path: Path) -> None:
    sample_lines = [
        "DrugName_SAMPLE_1",
        "DrugName_SAMPLE_2",
        "DrugName_SAMPLE_3",
        "DrugName_SAMPLE_4",
        "DrugName_SAMPLE_5",
    ]
    with (path / "sample_submission.txt").open("w", encoding="utf-8") as handle:
        handle.write("\n".join(sample_lines) + "\n")


def _write_answer_file(path: Path) -> None:
    with (path / "answer.txt").open("w", encoding="utf-8") as handle:
        handle.write("\n".join(GOLD_TOP5) + "\n")


def prepare(raw: Path, public: Path, private: Path) -> None:
    global DATA_DIR, DAVIS_DIR
    DATA_DIR = raw / "dti"
    DAVIS_DIR = DATA_DIR / "DAVIS"
    print("=" * 60)
    print("Preparing ScienceBench Task 12: DAVIS DTI repurposing")
    print("=" * 60)
    print("Raw directory:", raw)
    print("Public directory:", public)
    print("Private directory:", private)

    _ensure_dir(public)
    _ensure_dir(private)

    required_files = [
        DAVIS_DIR / "affinity_train.csv",
        DAVIS_DIR / "affinity_val.csv",
        DAVIS_DIR / "drug_train.txt",
        DAVIS_DIR / "drug_val.txt",
        DAVIS_DIR / "target_seq.json",
        DATA_DIR / "antiviral_drugs.tab",
        DATA_DIR / "covid_seq.txt",
    ]

    missing = [str(f) for f in required_files if not f.exists()]
    if missing:
        raise FileNotFoundError("Missing dataset files: " + ", ".join(missing))

    for file_path in required_files:
        target = public / file_path.relative_to(DATA_DIR.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
    print("✓ Copied DAVIS dataset and antiviral inputs to public directory")

    _write_sample_submission(public)
    print("✓ Wrote sample_submission.txt")

    _write_answer_file(private)
    print("✓ Wrote answer.txt")

    print("Preparation complete. Expected submission file:", OUTPUT_FILENAME)


if __name__ == "__main__":
    raise SystemExit("Use this module via the benchmark preparation tooling.")
