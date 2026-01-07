import logging
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_log_error, accuracy_score

from dsat.benchmarks.base import BaseBenchmarkEvaluator

logger = logging.getLogger(__name__)

class KaggleEvaluator(BaseBenchmarkEvaluator):
    """
    Evaluates artifacts from Kaggle-like tasks by comparing a generated
    submission file against a ground truth file.
    """

    def _calculate_rmsle(self, y_true, y_pred) -> float:
        """Calculates Root Mean Squared Logarithmic Error."""
        return np.sqrt(mean_squared_log_error(y_true, y_pred))

    def _calculate_accuracy(self, y_true, y_pred) -> float:
        """Calculates accuracy score."""
        return accuracy_score(y_true, y_pred)

    async def evaluate(self) -> Dict[str, Any]:
        """
        Loads submission and ground truth files, merges them, and computes the
        configured performance metric.
        """
        metric_name = self.config.get("metric", "rmsle")
        submission_filename = self.config.get("submission_file", "submission.csv")
        ground_truth_filename = self.config.get("ground_truth_file")

        submission_path = self.workspace.get_path("artifacts") / submission_filename
        ground_truth_path = self.benchmark_path / ground_truth_filename

        if not submission_path.exists():
            logger.error(f"Evaluation failed: Submission file not found at {submission_path}")
            return {"error": "Submission file not found."}
        if not ground_truth_path.exists():
            logger.error(f"Evaluation failed: Ground truth file not found at {ground_truth_path}")
            return {"error": "Ground truth file not found."}

        try:
            submission_df = pd.read_csv(submission_path)
            truth_df = pd.read_csv(ground_truth_path)
        except Exception as e:
            logger.error(f"Failed to read CSV files for evaluation: {e}")
            return {"error": f"Failed to read CSVs: {e}"}

        # Merge predictions and ground truth on the ID column
        # Assumes standard Kaggle format with 'Id' or 'PassengerId'
        id_col = next((col for col in submission_df.columns if col.lower() in ['id', 'passengerid']), None)
        if not id_col:
            return {"error": "No ID column found in submission file."}

        merged_df = pd.merge(submission_df, truth_df, on=id_col, how="left")

        # Get target column name (e.g., 'SalePrice', 'Survived') from ground truth df
        target_col = next((col for col in truth_df.columns if col != id_col), None)
        if not target_col:
            return {"error": "Could not determine target column from ground truth file."}
        
        # Suffix '_x' is prediction, '_y' is ground truth from pandas merge
        y_pred = merged_df[f"{target_col}_x"]
        y_true = merged_df[f"{target_col}_y"]

        if y_true.isnull().any():
            logger.warning("Ground truth contains null values after merging. Some predictions could not be scored.")
            # Drop rows where ground truth is missing to avoid errors
            valid_indices = y_true.notna()
            y_pred = y_pred[valid_indices]
            y_true = y_true[valid_indices]

        score = 0.0
        if metric_name == "rmsle":
            score = self._calculate_rmsle(y_true, y_pred)
        elif metric_name == "accuracy":
            score = self._calculate_accuracy(y_true, y_pred)
        else:
            return {"error": f"Unsupported metric: {metric_name}"}
        
        logger.info(f"Evaluation successful. Metric '{metric_name}': {score:.4f}")
        return {metric_name: score}