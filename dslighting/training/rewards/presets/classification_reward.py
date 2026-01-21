"""
分类任务奖励函数
"""
from dslighting.training.rewards.base import MetricBasedReward


class ClassificationReward(MetricBasedReward):
    """
    分类任务奖励（使用 accuracy）
    """

    def __init__(self):
        super().__init__(
            metric_name="accuracy",
            higher_is_better=True,
        )


__all__ = ["ClassificationReward"]
