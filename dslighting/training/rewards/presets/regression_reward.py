"""
回归任务奖励函数
"""
from dslighting.training.rewards.base import MetricBasedReward


class RegressionReward(MetricBasedReward):
    """
    回归任务奖励（使用 RMSE，越小越好）
    """

    def __init__(self):
        super().__init__(
            metric_name="rmse",
            higher_is_better=False,
        )


__all__ = ["RegressionReward"]
