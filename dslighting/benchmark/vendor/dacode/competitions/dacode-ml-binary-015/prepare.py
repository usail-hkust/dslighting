from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy test data
    test_file = raw / 'test.csv'
    if test_file.exists():
        shutil.copy2(test_file, public / 'test.csv')
        test_df = pd.read_csv(test_file)
        num_rows = len(test_df)

        # Create answer.csv and sample_submission.csv
        answer_df = pd.DataFrame({'CLASS': [0] * num_rows})
        answer_df.to_csv(private / 'answer.csv', index=False)
        sample_df = pd.DataFrame({'CLASS': [0] * num_rows})
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy clinvar data for reference
    clinvar_file = raw / 'clinvar_conflicting.csv'
    if clinvar_file.exists():
        shutil.copy2(clinvar_file, public / 'clinvar.csv')

    # Copy README
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
