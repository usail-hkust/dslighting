"""
奖励函数基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class RewardEvaluator(ABC):
    """奖励评估器基类"""

    @abstractmethod
    def evaluate(
        self,
        result: Any,
        task: Dict[str, Any],
    ) -> float:
        """
        评估结果并返回奖励值

        Parameters
        ----------
        result : Any
            Agent 执行结果
        task : Dict[str, Any]
            任务信息

        Returns
        -------
        float
            奖励值（通常在 [0, 1] 范围）
        """
        pass


class MetricBasedReward(RewardEvaluator):
    """
    基于指标的奖励函数

    将指标值归一化到 [0, 1] 范围
    """

    def __init__(
        self,
        metric_name: str,
        higher_is_better: bool = True,
        baseline: float = None,
        target: float = None,
    ):
        """
        Parameters
        ----------
        metric_name : str
            指标名称 (e.g., "accuracy", "f1", "rmse")
        higher_is_better : bool
            是否越大越好
        baseline : float
            基线值，用于归一化
        target : float
            目标值，用于归一化
        """
        self.metric_name = metric_name
        self.higher_is_better = higher_is_better
        self.baseline = baseline
        self.target = target

    def evaluate(self, result, task) -> float:
        # 获取指标值
        metric_value = result.metadata.get(self.metric_name, 0.0)

        # 归一化到 [0, 1]
        if self.higher_is_better:
            if self.target is not None and self.baseline is not None:
                reward = (metric_value - self.baseline) / (self.target - self.baseline)
            else:
                # 简单归一化：假设指标在 [0, 1]
                reward = metric_value
        else:
            # 对于越小越好的指标（如 RMSE）
            if self.target is not None and self.baseline is not None:
                reward = (self.baseline - metric_value) / (self.baseline - self.target)
            else:
                reward = 1.0 - metric_value

        return float(max(0.0, min(1.0, reward)))


__all__ = [
    "RewardEvaluator",
    "MetricBasedReward",
]
