from pathlib import Path
import shutil

GOLD_DIR = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "dm-csv-006"
SKIP_FROM_PUBLIC = {'README.md', 'result.csv', 'sample.txt'}


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

    # 创建 sample_submission.csv（只用 header，无数据泄露）
    answer_csv = private / "answer.csv"
    if answer_csv.exists():
        with open(answer_csv, encoding="utf-8") as f:
            header_line = f.readline()
        with open(public / "sample_submission.csv", "w", encoding="utf-8") as f:
            f.write(header_line)
