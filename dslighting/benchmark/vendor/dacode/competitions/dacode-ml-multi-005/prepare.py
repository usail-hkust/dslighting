from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Read training data
    gold_file = raw / 'train.txt'
    if gold_file.exists():
        gold_df = pd.read_csv(gold_file, sep=';', header=None, names=['text', 'emotion'])
        gold_df.to_csv(public / 'train.csv', index=False)

    # Copy test data
    test_file = raw / 'test.txt'
    if test_file.exists():
        test_df = pd.read_csv(test_file, sep=';', header=None, names=['text', 'emotion'])
        test_df = test_df[['text']].copy()
        test_df.to_csv(public / 'test.csv', index=False)

    # Copy answer from gold directory
    gold_answer = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-multi-005" / "emotions.csv"
    if gold_answer.exists():
        shutil.copy2(gold_answer, private / 'answer.csv')

        df = pd.read_csv(gold_answer)
        first_vals = df.iloc[0].values
        placeholder_df = pd.DataFrame([first_vals] * len(df), columns=df.columns)
        placeholder_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy validation data
    val_file = raw / 'val.txt'
    if val_file.exists():
        val_df = pd.read_csv(val_file, sep=';', header=None, names=['text', 'emotion'])
        val_df.to_csv(public / 'val.csv', index=False)
