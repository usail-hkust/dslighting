"""
指标计算工具
"""
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
)


def calculate_metric(y_true, y_pred, metric_name: str) -> float:
    """
    计算指定指标

    Parameters
    ----------
    y_true : array-like
        真实值
    y_pred : array-like
        预测值
    metric_name : str
        指标名称

    Returns
    -------
    float
        指标值
    """
    if metric_name == "accuracy":
        return accuracy_score(y_true, y_pred)
    elif metric_name == "f1":
        return f1_score(y_true, y_pred, average='macro')
    elif metric_name == "precision":
        return precision_score(y_true, y_pred, average='macro')
    elif metric_name == "recall":
        return recall_score(y_true, y_pred, average='macro')
    elif metric_name == "rmse":
        return np.sqrt(mean_squared_error(y_true, y_pred))
    elif metric_name == "mae":
        return mean_absolute_error(y_true, y_pred)
    elif metric_name == "r2":
        return r2_score(y_true, y_pred)
    else:
        raise ValueError(f"Unknown metric: {metric_name}")


__all__ = ["calculate_metric"]
