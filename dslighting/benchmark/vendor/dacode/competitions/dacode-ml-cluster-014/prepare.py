from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Read gold file
    gold_file = raw / 'cluster.csv'
    if not gold_file.exists():
        # Try other names
        for name in ['result.csv', 'clustering.csv']:
            if (raw / name).exists():
                gold_file = raw / name
                break

    if gold_file.exists():
        gold_df = pd.read_csv(gold_file)
        # Find the cluster column (could be 'Cluster' or 'Clusters')
        cluster_cols = [c for c in gold_df.columns if c.lower().startswith('cluster')]
        if cluster_cols:
            cluster_col = cluster_cols[0]
            # Create test.csv with only Feature columns
            feature_cols = [c for c in gold_df.columns if c != cluster_col]
            test_df = gold_df[feature_cols].copy()
            test_df.to_csv(public / 'test.csv', index=False)

            # Create answer.csv with full data
            gold_df.to_csv(private / 'answer.csv', index=False)

            # Create sample_submission.csv with placeholder Cluster values
            sample_df = gold_df.copy()
            cluster_placeholder = gold_df[cluster_col].iloc[0]
            sample_df[cluster_col] = cluster_placeholder
            sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy train data if exists
    for train_name in ['Mall_Customers.csv', 'train.csv', 'marketing_campaign.csv']:
        train_file = raw / train_name
        if train_file.exists():
            shutil.copy2(train_file, public / 'train.csv')
            break

    # Copy README if exists
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')