import pandas as pd
import numpy as np


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Grade the submission using MSE metric.

    Args:
        submission: DataFrame with columns ['id', 'pred_0', 'pred_1', ..., 'pred_167']
                   Each row represents one test sample
                   Columns pred_0 to pred_167 represent flattened predictions (24 timesteps * 7 features)
        answers: DataFrame with columns ['id', 'pred_0', 'pred_1', ..., 'pred_167']
                Ground truth in same format as submission

    Returns:
        MSE score (float) - lower is better
    """
    try:
        # Extract prediction columns (pred_0 to pred_167 for 24*7=168 values)
        pred_cols = [f'pred_{i}' for i in range(24 * 7)]

        # Check if all required columns exist
        if not all(col in submission.columns for col in pred_cols):
            print(f"Error: Missing prediction columns. Expected columns: {pred_cols[:5]}...{pred_cols[-5:]}")
            return float(1e10)

        # Sort by id to ensure alignment
        submission = submission.sort_values('id').reset_index(drop=True)
        answers = answers.sort_values('id').reset_index(drop=True)

        # Extract predictions
        predictions = submission[pred_cols].values
        ground_truth = answers[pred_cols].values

        # Reshape to (N, 24, 7) for MSE calculation
        predictions_3d = predictions.reshape(-1, 24, 7)
        ground_truth_3d = ground_truth.reshape(-1, 24, 7)

        # Ensure shapes match
        if predictions_3d.shape != ground_truth_3d.shape:
            print(f"Error: Shape mismatch. Got {predictions_3d.shape}, expected {ground_truth_3d.shape}")
            return float(1e10)

        # Calculate MSE (primary metric)
        mse = np.mean((predictions_3d - ground_truth_3d) ** 2)

        # Calculate MAE (for logging/debugging)
        mae = np.mean(np.abs(predictions_3d - ground_truth_3d))

        print(f"MSE: {mse:.6f}, MAE: {mae:.6f}")

        return float(mse)

    except Exception as e:
        print(f"Error during grading: {e}")
        import traceback
        traceback.print_exc()
        # Return a very high score (bad) on error
        return float(1e10)
