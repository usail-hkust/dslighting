import pandas as pd
import numpy as np
import sys
from pathlib import Path


def prepare(raw: Path, public: Path, private: Path):
    """
    Prepare the ILI dataset for the benchmark.

    This function converts the CSV time series data to numpy arrays for
    time series forecasting.

    Args:
        raw: Path to raw data directory (contains national_illness.csv)
        public: Path to public directory (visible to participants)
        private: Path to private directory (hidden from participants, used for grading)
    """
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
            X_train, y_train = get_dataset('train')
            X_test, y_test = get_dataset('test')

            print(f"Loaded training data: X_train.shape = {X_train.shape}, y_train.shape = {y_train.shape}")
            print(f"Loaded test data: X_test.shape = {X_test.shape}, y_test.shape = {y_test.shape}")

            # Save training data as numpy arrays in public directory
            np.save(public / "train_input.npy", X_train)
            np.save(public / "train_target.npy", y_train)

            # Save test input (without targets) in public directory
            np.save(public / "test_input.npy", X_test)

            # Save test targets for grading (private)
            # Save as both numpy (for convenience) and CSV (for framework compatibility)
            np.save(private / "test_targets.npy", y_test)

            # Also save as CSV for framework compatibility
            test_targets_flat = y_test.reshape(len(y_test), -1)
            test_targets_df = pd.DataFrame(test_targets_flat,
                                          columns=[f'pred_{i}' for i in range(24 * 7)])
            test_targets_df.insert(0, 'id', range(len(y_test)))
            test_targets_df.to_csv(private / "test_targets.csv", index=False)

            # Create sample submission CSV file
            # Flatten (N, 24, 7) to (N, 168) where 168 = 24*7
            sample_submission_flat = np.zeros((len(y_test), 24 * 7))
            sample_submission_df = pd.DataFrame(sample_submission_flat,
                                               columns=[f'pred_{i}' for i in range(24 * 7)])
            sample_submission_df.insert(0, 'id', range(len(y_test)))
            sample_submission_df.to_csv(public / "sample_submission.csv", index=False)

            # Also save numpy version for convenience
            np.save(public / "sample_submission.npy", np.zeros_like(y_test))

            print(f"Data preparation completed:")
            print(f"  - Training: {len(X_train)} samples")
            print(f"  - Test: {len(X_test)} samples")
            print(f"  - Input sequence length: {X_train.shape[1]}")
            print(f"  - Input features: {X_train.shape[2]}")
            print(f"  - Output sequence length: {y_train.shape[1]}")
            print(f"  - Output features: {y_train.shape[2]}")

        finally:
            os.chdir(original_dir)
            sys.path.remove(str(raw))

    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: create dummy files if loading fails
        print("Creating dummy submission files...")
        dummy_array = np.zeros((1, 24, 7))
        np.save(private / "test_targets.npy", dummy_array)
        np.save(public / "sample_submission.npy", dummy_array)

    # Validation checks
    assert (public / "train_input.npy").exists(), "Training input should exist"
    assert (public / "train_target.npy").exists(), "Training target should exist"
    assert (public / "test_input.npy").exists(), "Test input should exist"
    assert (private / "test_targets.npy").exists(), "Test targets should exist"
    assert (public / "sample_submission.npy").exists(), "Sample submission should exist"

    print(f"\nPrepared ILI dataset:")
    print(f"  - Public files: {list(public.glob('*'))}")
    print(f"  - Private files: {list(private.glob('*'))}")
