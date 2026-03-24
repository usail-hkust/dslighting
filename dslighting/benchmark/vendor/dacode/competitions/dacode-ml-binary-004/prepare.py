from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy test data (what participants predict on)
    test_file = raw / 'test.csv'
    if test_file.exists():
        shutil.copy2(test_file, public / 'test.csv')

    # Copy train data with answer column
    train_file = raw / 'train.csv'
    if train_file.exists():
        shutil.copy2(train_file, public / 'train.csv')
        # Extract answer from train.csv based on PassengerId matching test.csv
        if test_file.exists():
            test_df = pd.read_csv(test_file)
            train_df = pd.read_csv(train_file)
            # Merge to get Transported for test rows
            if 'PassengerId' in test_df.columns and 'Transported' in train_df.columns:
                merged = test_df[['PassengerId']].merge(train_df[['PassengerId', 'Transported']], on='PassengerId', how='left')
                answer_df = merged[['Transported']].fillna(False)
                answer_df.to_csv(private / 'answer.csv', index=False)

    # Create sample_submission.csv based on test.csv
    if test_file.exists():
        test_df = pd.read_csv(test_file)
        num_rows = len(test_df)
        if 'PassengerId' in test_df.columns:
            ids = test_df['PassengerId'].tolist()
        else:
            ids = list(range(num_rows))
        sample_df = pd.DataFrame({'PassengerId': ids, 'Transported': [False] * num_rows})
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy README if exists
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
