import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score


def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """
    Grade the submission using accuracy metric.

    Args:
        submission: DataFrame with columns ['id', 'label']
        answers: DataFrame with columns ['id', 'label']

    Returns:
        Accuracy score (float between 0 and 1)
    """
    # Merge on id to ensure alignment
    merged = pd.merge(answers, submission, on='id', suffixes=('_true', '_pred'))

    # Calculate accuracy
    accuracy = accuracy_score(merged['label_true'], merged['label_pred'])

    return accuracy
