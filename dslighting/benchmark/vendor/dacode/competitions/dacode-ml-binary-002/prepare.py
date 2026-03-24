from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy test data (what participants predict on)
    test_file = raw / 'test.csv'
    if test_file.exists():
        test_df = pd.read_csv(test_file)
        # Extract Response to answer.csv if available
        if 'Response' in test_df.columns:
            answer_df = test_df[['id', 'Response']].copy()
            answer_df.to_csv(private / 'answer.csv', index=False)
            # Remove Response from test for public
            test_features = test_df.drop(columns=['Response'])
            test_features.to_csv(public / 'test.csv', index=False)
        else:
            shutil.copy2(test_file, public / 'test.csv')
            # Create answer.csv from test.csv ids with placeholder Response
            num_rows = len(test_df)
            if 'id' in test_df.columns:
                ids = test_df['id'].tolist()
            else:
                ids = list(range(num_rows))
            answer_df = pd.DataFrame({'id': ids, 'Response': [0] * num_rows})
            answer_df.to_csv(private / 'answer.csv', index=False)

    # Create sample_submission.csv based on test.csv
    if test_file.exists():
        test_df = pd.read_csv(test_file)
        num_rows = len(test_df)
        if 'id' in test_df.columns:
            ids = test_df['id'].tolist()
        else:
            ids = list(range(num_rows))
        sample_sub = pd.DataFrame({'id': ids, 'Response': [0] * num_rows})
        sample_sub.to_csv(public / 'sample_submission.csv', index=False)

    # Copy train data to public for reference
    train_file = raw / 'train.csv'
    if train_file.exists():
        shutil.copy2(train_file, public / 'train.csv')

    # Copy README if exists
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
