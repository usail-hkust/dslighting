from pathlib import Path
import shutil


def prepare(raw: Path, public: Path, private: Path) -> Path:
    """
    Prepare Titanic dataset layout under `public/` and `private/`.

    This function is primarily for compatibility with the MLE-Bench interface.
    In many local evaluation flows, the dataset is already prepared and this
    function won't be used.
    """
    # Best-effort copy if raw contains canonical kaggle files.
    # We intentionally keep this minimal to avoid over-coupling.
    train = raw / "train.csv"
    test = raw / "test.csv"
    sample = raw / "gender_submission.csv"

    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    if train.exists():
        shutil.copy2(train, public / "train.csv")
    if test.exists():
        shutil.copy2(test, public / "test.csv")
    if sample.exists():
        # Kaggle's provided sample submission is often named `gender_submission.csv`.
        shutil.copy2(sample, public / "sampleSubmission.csv")

    # We cannot generate private answers without ground truth; leave it to the dataset provider.
    return public

