"""
DSLighting Training - Agent-Lightning 训练集成

提供与 Microsoft Agent-Lightning 的集成，用于训练 data science agents。
"""
try:
    # ========== Agents ==========
    from dslighting.training.agents.lit_ds_agent import LitDSAgent

    # ========== Rewards ==========
    from dslighting.training.rewards.base import RewardEvaluator
    from dslighting.training.rewards.presets import (
        KaggleReward,
        ClassificationReward,
        RegressionReward,
    )

    # ========== Datasets ==========
    from dslighting.training.datasets.converters import DatasetConverter

    # ========== Config ==========
    from dslighting.training.config.verl_config import VerlConfigBuilder

except ImportError:
    # Agent-Lightning 或其他依赖不可用
    LitDSAgent = None
    RewardEvaluator = None
    KaggleReward = None
    ClassificationReward = None
    RegressionReward = None
    DatasetConverter = None
    VerlConfigBuilder = None

__all__ = [
    # Agents
    "LitDSAgent",
    # Rewards
    "RewardEvaluator",
    "KaggleReward",
    "ClassificationReward",
    "RegressionReward",
    # Datasets
    "DatasetConverter",
    # Config
    "VerlConfigBuilder",
]
