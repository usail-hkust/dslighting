from pathlib import Path
import shutil, pandas as pd

def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    # Copy answer from gold directory
    gold_answer = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "ml-cluster-005" / "cluster.csv"
    if gold_answer.exists():
        gold_df = pd.read_csv(gold_answer)

        # Find the cluster column
        cluster_cols = [c for c in gold_df.columns if c.lower().startswith('cluster')]
        if cluster_cols:
            cluster_col = cluster_cols[0]
            # Create test.csv with only Feature columns
            feature_cols = [c for c in gold_df.columns if c != cluster_col]
            test_df = gold_df[feature_cols].copy()
            test_df.to_csv(public / 'test.csv', index=False)

        # Copy answer from gold
        shutil.copy2(gold_answer, private / 'answer.csv')

        # Create sample_submission with placeholder Cluster values
        sample_df = gold_df.copy()
        cluster_placeholder = gold_df[cluster_col].iloc[0] if cluster_cols else 0
        sample_df[cluster_col] = cluster_placeholder
        sample_df.to_csv(public / 'sample_submission.csv', index=False)

    # Copy train data if exists
    for train_name in ['blob_dataset.csv', 'genres_v2.csv', 'playlists.csv', 'circle_data.csv', 'train.csv']:
        train_file = raw / train_name
        if train_file.exists():
            shutil.copy2(train_file, public / 'train.csv')
            break

    # Copy README if exists
    readme = raw / 'README.md'
    if readme.exists():
        shutil.copy2(readme, public / 'README.md')
