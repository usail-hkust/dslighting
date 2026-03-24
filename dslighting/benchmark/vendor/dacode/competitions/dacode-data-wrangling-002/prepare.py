from pathlib import Path
import shutil

SUBMISSION_FILENAME = "sample_submission.csv"

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # 1. 复制所有 source 文件到 public/（排除 _* 前缀文件）
    for f in raw.iterdir():
        if f.is_file() and not f.name.startswith("_"):
            shutil.copy2(f, public / f.name)

    # 2. 裁剪提交模板为 header-only
    template = public / SUBMISSION_FILENAME
    if template.exists():
        header = template.read_text().splitlines()[0]
        template.write_text(header + "\n")

    # 3. gold → private/answer.csv（gold 在 gold/ 目录）
    gold = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-wrangling-002" / SUBMISSION_FILENAME
    if gold.exists():
        shutil.copy2(gold, private / "answer.csv")
