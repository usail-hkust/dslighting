from pathlib import Path
import shutil

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-015"
SKIP_FROM_PUBLIC = {"README.md", "result.csv", "sample_result.csv"}


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # 复制数据文件到 public
    for f in raw.iterdir():
        if f.is_file() and f.name not in SKIP_FROM_PUBLIC:
            shutil.copy2(f, public / f.name)

    # 从 gold 复制答案到 private/answer.csv
    gold_src = GOLD_DIR / "result.csv"
    if gold_src.exists():
        shutil.copy2(gold_src, private / "answer.csv")

    # 使用 raw 的 sample_result.csv 作为 sample_submission.csv
    sample_template = raw / "sample_result.csv"
    if sample_template.exists():
        shutil.copy2(sample_template, public / "sample_submission.csv")
