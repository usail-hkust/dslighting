import pandas as pd
import numpy as np
import sys
from pathlib import Path


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the ethanol-concentration dataset for the benchmark.

    This function converts the .ts time series files to numpy arrays,
    so that public directory only contains data, not data loading code.

    Args:
        raw: Path to raw data directory (contains EthanolConcentration_TRAIN.ts and EthanolConcentration_TEST.ts)
        public: Path to public directory (visible to participants)
        private: Path to private directory (hidden from participants, used for grading)
    """
    # Load test data to extract labels for grading
    try:
        # Add raw directory to path temporarily to import dataset module
        sys.path.insert(0, str(raw))

        # Use the local dataset module to load data
        from dataset import get_dataset

        # Change to raw directory to load data
        import os
        original_dir = os.getcwd()
        os.chdir(str(raw))

        try:
            # Load train and test datasets
            X_train, y_train = get_dataset('TRAIN')
            X_test, y_test = get_dataset('TEST')

            print(f"Loaded training data: X_train.shape = {X_train.shape}, y_train.shape = {y_train.shape}")
            print(f"Loaded test data: X_test.shape = {X_test.shape}, y_test.shape = {y_test.shape}")
            print(f"Number of unique labels: {len(np.unique(y_train))}")

            # Save training data as numpy arrays in public directory
            np.save(public / "train_data.npy", X_train)
            np.save(public / "train_labels.npy", y_train.flatten())

            # Save test data (without labels) in public directory
            np.save(public / "test_data.npy", X_test)

            # Create test labels dataframe for grading (private)
            test_labels_df = pd.DataFrame(
                {"id": range(len(y_test)), "label": y_test.flatten()}
            )
            test_labels_df.to_csv(private / "test_labels.csv", index=False)

            # Create sample submission file
            sample_submission = pd.DataFrame(
                {"id": range(len(y_test)), "label": 0}  # Default to class 0
            )
            sample_submission.to_csv(public / "sample_submission.csv", index=False)

            print(f"Data preparation completed:")
            print(f"  - Training: {len(X_train)} samples")
            print(f"  - Test: {len(X_test)} samples")
            print(f"  - Sequence length: {X_train.shape[1]}")
            print(f"  - Feature dimension: {X_train.shape[2]}")
            print(f"  - Number of classes: {len(np.unique(y_train))}")

        finally:
            os.chdir(original_dir)
            sys.path.remove(str(raw))

    except Exception as e:
        print(f"Error loading test labels: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: create dummy files if loading fails
        print("Creating dummy submission files...")
        dummy_df = pd.DataFrame({"id": [0], "label": [0]})
        dummy_df.to_csv(private / "test_labels.csv", index=False)
        dummy_df.to_csv(public / "sample_submission.csv", index=False)

    # Validation checks
    assert (public / "train_data.npy").exists(), "Training data should exist"
    assert (public / "train_labels.npy").exists(), "Training labels should exist"
    assert (public / "test_data.npy").exists(), "Test data should exist"
    assert (private / "test_labels.csv").exists(), "Test labels should exist"
    assert (public / "sample_submission.csv").exists(), "Sample submission should exist"

    print(f"\nPrepared ethanol-concentration dataset:")
    print(f"  - Public files: {list(public.glob('*'))}")
    print(f"  - Private files: {list(private.glob('*'))}")
