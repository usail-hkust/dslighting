from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Gold file is submission.csv
    gold_file = raw / 'submission.csv'

    if gold_file.exists():
        gold_df = pd.read_csv(gold_file)
        # 保存answer.csv（真实答案）
        gold_df.to_csv(private / 'answer.csv', index=False)

        # 创建sample_submission.csv（占位符）
        # 使用gold的列结构，但用占位符值替换预测列
        sample_df = gold_df.copy()
        pred_cols = [c for c in gold_df.columns if c.lower() != 'id']

        for col in pred_cols:
            if pd.api.types.is_numeric_dtype(gold_df[col]):
                sample_df[col] = 0
            else:
                sample_df[col] = gold_df[col].iloc[0]
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

        # 复制测试数据
        test_file = raw / 'test.csv'
        if test_file.exists():
            shutil.copy2(test_file, public / 'test.csv')
    else:
        # 没有gold文件时，创建空的Sample_submission
        (public / 'sample_submission.csv').write_text('id,Exited\n')

    # 复制训练数据
    train_file = raw / 'train.csv'
    if train_file.exists():
        shutil.copy2(train_file, public / 'train.csv')

    # 复制README
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
