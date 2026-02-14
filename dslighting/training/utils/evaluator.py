"""
Evaluation Utilities

Utilities for computing evaluation metrics and scores.
"""
from typing import Any, Callable, Dict, Optional
import numpy as np


class Evaluator:
    """
    Utility class for computing evaluation metrics.

    Provides common metrics for evaluating model predictions
    against ground truth values.
    """

    # Supported metric functions
    METRICS: Dict[str, Callable[..., float]] = {
        "accuracy": lambda pred, gt: np.mean(np.array(pred) == np.array(gt)) if hasattr(pred, '__len__') else (1.0 if pred == gt else 0.0),
        "mae": lambda pred, gt: float(np.mean(np.abs(np.array(pred) - np.array(gt)))),
        "mse": lambda pred, gt: float(np.mean((np.array(pred) - np.array(gt)) ** 2)),
        "rmse": lambda pred, gt: float(np.sqrt(np.mean((np.array(pred) - np.array(gt)) ** 2))),
    }

    @staticmethod
    def compute_score(
        predictions: Any,
        ground_truth: Any,
        metric: str = "accuracy",
        **kwargs
    ) -> float:
        """
        Compute evaluation score using the specified metric.

        Parameters
        ----------
        predictions : Any
            Model predictions.
        ground_truth : Any
            Ground truth labels/values.
        metric : str, optional
            Name of the metric to compute. Defaults to "accuracy".
            Supported: "accuracy", "mae", "mse", "rmse".
        **kwargs
            Additional metric-specific parameters.

        Returns
        -------
        float
            Computed score. Returns 0.0 if metric is unsupported.
        """
        # Convert inputs to numpy arrays for consistent handling
        pred_arr = np.array(predictions)
        gt_arr = np.array(ground_truth)

        # Get metric function, default to accuracy
        metric_func = Evaluator.METRICS.get(metric.lower())

        if metric_func is not None:
            try:
                return float(metric_func(pred_arr, gt_arr))
            except (ValueError, TypeError):
                # Handle edge cases like mismatched shapes
                return 0.0

        # Unknown metric
        return 0.0

    @staticmethod
    def list_metrics() -> list:
        """
        List available metric names.

        Returns
        -------
        list
            List of supported metric names.
        """
        return list(Evaluator.METRICS.keys())


__all__ = ["Evaluator"]
