"""
Kaggle 竞赛奖励函数
"""
from dslighting.training.rewards.base import MetricBasedReward


class KaggleReward(MetricBasedReward):
    """
    Kaggle 竞赛奖励

    根据不同任务类型使用不同指标
    """

    def __init__(self, task_type: str = "auto"):
        """
        Parameters
        ----------
        task_type : str
            任务类型: "classification", "regression", "auto"
        """
        self.task_type = task_type

    def evaluate(self, result, task) -> float:
        # 自动检测任务类型
        if self.task_type == "auto":
            metric_name = self._detect_metric(task)
            higher_is_better = self._is_higher_better(metric_name)
        else:
            metric_name, higher_is_better = self._get_metric_for_type(self.task_type)

        # 创建临时评估器
        evaluator = MetricBasedReward(
            metric_name=metric_name,
            higher_is_better=higher_is_better,
        )
        return evaluator.evaluate(result, task)

    def _detect_metric(self, task):
        """根据任务元数据检测指标"""
        eval_metric = task.get("metadata", {}).get("eval_metric")
        if eval_metric:
            return eval_metric
        return "accuracy"  # 默认

    def _is_higher_better(self, metric_name):
        """判断指标是否越大越好"""
        higher_better_metrics = {
            "accuracy", "f1", "precision", "recall",
            "auc", "r2", "roc_auc"
        }
        return metric_name in higher_better_metrics

    def _get_metric_for_type(self, task_type):
        """根据任务类型返回指标"""
        if task_type == "classification":
            return "accuracy", True
        elif task_type == "regression":
            return "rmse", False
        else:
            return "accuracy", True


__all__ = ["KaggleReward"]
