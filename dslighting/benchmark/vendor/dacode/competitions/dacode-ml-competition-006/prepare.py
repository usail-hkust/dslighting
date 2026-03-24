from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Gold文件在raw目录（如果有）或从gold目录复制
    gold_file = raw / 'submission.csv'

    if gold_file.exists():
        gold_df = pd.read_csv(gold_file)
        # 保存answer.csv（真实答案）
        gold_df.to_csv(private / 'answer.csv', index=False)

        # 创建sample_submission.csv（占位符）
        sample_df = gold_df.copy()
        pred_cols = [c for c in gold_df.columns if c.lower() != 'id' and c.lower() != 'id']

        for col in pred_cols:
            if pd.api.types.is_numeric_dtype(gold_df[col]):
                sample_df[col] = 0
            else:
                sample_df[col] = gold_df[col].iloc[0]
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # 复制训练和测试数据
    for fname in ['train.csv', 'test.csv']:
        f = raw / fname
        if f.exists():
            shutil.copy2(f, public / fname)

    # 复制README
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
