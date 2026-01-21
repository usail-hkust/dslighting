"""
DSLighting Training Rewards - Presets

预设的奖励函数
"""
from dslighting.training.rewards.presets.kaggle_reward import KaggleReward
from dslighting.training.rewards.presets.classification_reward import ClassificationReward
from dslighting.training.rewards.presets.regression_reward import RegressionReward

__all__ = [
    "KaggleReward",
    "ClassificationReward",
    "RegressionReward",
]
