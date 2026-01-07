import pandas as pd
import numpy as np


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Score a house price submission using RMSE.

    Args:
        submission: Predictions with columns [house_id, predicted_price].
        answers: Ground truth with columns [house_id, actual_price].

    Returns:
        float: RMSE score (lower is better). Returns inf if invalid.
    """
    try:
        # Validate columns
        required_sub_cols = {'house_id', 'predicted_price'}
        required_ans_cols = {'house_id', 'actual_price'}

        if not required_sub_cols.issubset(submission.columns):
            print(f"❌ Submission missing columns: {required_sub_cols - set(submission.columns)}")
            return float('inf')

        if not required_ans_cols.issubset(answers.columns):
            print(f"❌ Answer file missing columns: {required_ans_cols - set(answers.columns)}")
            return float('inf')

        # Join on house_id
        merged = submission.merge(
            answers,
            on='house_id',
            how='inner',
            suffixes=('_sub', '_ans')
        )

        # Ensure every house has a prediction
        if len(merged) != len(answers):
            missing_count = len(answers) - len(merged)
            print(f"⚠️  Warning: submission missing predictions for {missing_count} house(s)")
            return float('inf')

        # Validate predicted values
        if merged['predicted_price'].isna().any():
            print("❌ Predictions contain NaN")
            return float('inf')

        if (merged['predicted_price'] < 0).any():
            print("❌ Predictions contain negative values")
            return float('inf')

        # Compute RMSE
        rmse = np.sqrt(
            np.mean(
                (merged['predicted_price'] - merged['actual_price']) ** 2
            )
        )

        print(f"✓ RMSE: {rmse:.2f}")
        return float(rmse)

    except Exception as e:
        print(f"❌ Grading error: {e}")
        return float('inf')


if __name__ == "__main__":
    """Quick tests for the grader."""
    # Sample data
    test_submission = pd.DataFrame({
        'house_id': [1, 2, 3],
        'predicted_price': [250000.0, 350000.0, 420000.0]
    })

    test_answers = pd.DataFrame({
        'house_id': [1, 2, 3],
        'actual_price': [245000.0, 360000.0, 410000.0]
    })

    print("Testing grader:")
    print("=" * 60)
    score = grade(test_submission, test_answers)
    print(f"Test RMSE: {score:.2f}")

    # Invalid submission
    print("\nTesting invalid submission (missing house):")
    print("=" * 60)
    invalid_submission = pd.DataFrame({
        'house_id': [1, 2],  # house_id=3 missing
        'predicted_price': [250000.0, 350000.0]
    })
    score = grade(invalid_submission, test_answers)
    print(f"Invalid submission RMSE: {score}")
