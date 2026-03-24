from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    test_file = raw / 'test.csv'
    if test_file.exists():
        test_df = pd.read_csv(test_file)

        # If Output column exists, use it for answer
        if 'Output' in test_df.columns:
            # Save answer to private
            answer_df = test_df[['Output']].copy()
            answer_df.columns = ['result']
            answer_df.to_csv(private / 'answer.csv', index=False)

            # Create test without Output for public
            cols_to_drop = ['Output']
            if 'Unnamed: 12' in test_df.columns:
                cols_to_drop.append('Unnamed: 12')
            test_features = test_df.drop(columns=cols_to_drop)
            test_features.to_csv(public / 'test.csv', index=False)
        else:
            # No Output column, just copy test as-is
            shutil.copy2(test_file, public / 'test.csv')

    # Copy README if exists
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')

    # Copy train data - try common train file names
    for train_name in ['onlinefoods.csv', 'train.csv', 'Train.csv']:
        train_file = raw / train_name
        if train_file.exists():
            shutil.copy2(train_file, public / 'train.csv')
            break

    # Create sample_submission.csv with placeholder rows matching test.csv
    if test_file.exists():
        num_rows = len(test_df)
        sample_df = pd.DataFrame({'result': ['Yes'] * num_rows})
        sample_df.to_csv(public / 'sample_submission.csv', index=False)
