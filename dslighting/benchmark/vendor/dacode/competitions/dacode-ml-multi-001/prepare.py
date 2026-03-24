from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy training data from raw
    gold_file = raw / 'activities.csv'
    if gold_file.exists():
        gold_df = pd.read_csv(gold_file)
        gold_df.to_csv(public / 'train.csv', index=False)

    # Copy test data
    test_file = raw / 'activity_test.csv'
    if test_file.exists():
        shutil.copy2(test_file, public / 'test.csv')

    # Copy answer from gold directory
    gold_answer = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-multi-001" / "activity.csv"
    if gold_answer.exists():
        shutil.copy2(gold_answer, private / 'answer.csv')

    # Sample submission (copy from gold answer)
    if gold_answer.exists():
        df = pd.read_csv(gold_answer)
        first_vals = df.iloc[0].values
        placeholder_df = pd.DataFrame([first_vals] * len(df), columns=df.columns)
        placeholder_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy time series data
    ts_file = raw / 'time_series_data_human_activities.csv'
    if ts_file.exists():
        shutil.copy2(ts_file, public / 'time_series_data_human_activities.csv')
