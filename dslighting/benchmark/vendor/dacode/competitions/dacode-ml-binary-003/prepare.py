from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy validation data (what participants predict on)
    validation_file = raw / 'twitter_validation.csv'
    test_file = raw / 'test.csv'
    if validation_file.exists():
        shutil.copy2(validation_file, public / 'test.csv')
        val_df = pd.read_csv(validation_file)
        num_rows = len(val_df)

        # Create answer.csv with placeholder labels
        answer_df = pd.DataFrame({'index': val_df['index'] if 'index' in val_df.columns else list(range(num_rows)), 'result': ['Positive'] * num_rows})
        answer_df.to_csv(private / 'answer.csv', index=False)

        # Create sample_submission.csv with same rows as test
        sample_df = pd.DataFrame({'index': val_df['index'] if 'index' in val_df.columns else list(range(num_rows)), 'result': ['Positive'] * num_rows})
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy twitter_training.csv as train.csv
    train_file = raw / 'twitter_training.csv'
    if train_file.exists():
        shutil.copy2(train_file, public / 'train.csv')

    # Copy README if exists
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
