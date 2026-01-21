"""
DSLighting Training Rewards
"""
from dslighting.training.rewards.base import RewardEvaluator
from dslighting.training.rewards.presets import (
    KaggleReward,
    ClassificationReward,
    RegressionReward,
)

__all__ = [
    "RewardEvaluator",
    "KaggleReward",
    "ClassificationReward",
    "RegressionReward",
]
