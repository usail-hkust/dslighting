from pathlib import Path
import shutil

# gold 目录
GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-001"


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # 复制数据文件到 public（跳过 README、weight_class.md、answer_ 文件、submission 模板）
    skip_files = {"README.md", "weight_class.md", "undefeated.csv"}
    skip_prefix = {"answer_"}  # 跳过 answer_ 开头的文件

    for f in raw.iterdir():
        if f.is_file():
            # 跳过明确指定的文件
            if f.name in skip_files:
                continue
            # 跳过 answer_ 开头的文件（答案泄露）
            if f.name.startswith("answer_"):
                continue
            shutil.copy2(f, public / f.name)

    # 把 gold 文件复制到 private/answer.csv
    gold_src = GOLD_DIR / "undefeated.csv"
    if gold_src.exists():
        shutil.copy2(gold_src, private / "answer.csv")

    # 复制 raw 的 undefeated.csv（只有 header）到 sample_submission.csv
    submission_template = raw / "undefeated.csv"
    if submission_template.exists():
        shutil.copy2(submission_template, public / "sample_submission.csv")
