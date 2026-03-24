from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy test data
    test_file = raw / 'Test.csv'
    if test_file.exists():
        shutil.copy2(test_file, public / 'test.csv')
        test_df = pd.read_csv(test_file)
        num_rows = len(test_df)

        # Create answer.csv and sample_submission.csv
        answer_df = pd.DataFrame({'Target': [0] * num_rows})
        answer_df.to_csv(private / 'answer.csv', index=False)
        sample_df = pd.DataFrame({'Target': [0] * num_rows})
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy sample_target if exists
    sample_file = raw / 'sample_target.csv'
    if sample_file.exists():
        shutil.copy2(sample_file, public / 'sample_target.csv')

    # Copy train data
    train_file = raw / 'Train.csv'
    if train_file.exists():
        shutil.copy2(train_file, public / 'train.csv')

    # Copy README
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
