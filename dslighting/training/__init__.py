"""
DSLighting Training - Agent-Lightning Training Integration

Provides integration with Microsoft Agent-Lightning for training data science agents.
"""
try:
    # ========== Agents ==========
    from dslighting.training.agents.lit_ds_agent import LitDSAgent
    from dslighting.training.agents.presets import (
        AIDETrainingAgent,
        AutoKaggleTrainingAgent,
        DataInterpreterTrainingAgent,
    )

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

    # ========== Utils ==========
    from dslighting.training.utils.tracer import TraceCollector
    from dslighting.training.utils.evaluator import Evaluator

except ImportError:
    # Agent-Lightning or other dependencies not available
    LitDSAgent = None
    AIDETrainingAgent = None
    AutoKaggleTrainingAgent = None
    DataInterpreterTrainingAgent = None
    RewardEvaluator = None
    KaggleReward = None
    ClassificationReward = None
    RegressionReward = None
    DatasetConverter = None
    VerlConfigBuilder = None
    TraceCollector = None
    Evaluator = None

__all__ = [
    # Agents
    "LitDSAgent",
    "AIDETrainingAgent",
    "AutoKaggleTrainingAgent",
    "DataInterpreterTrainingAgent",
    # Rewards
    "RewardEvaluator",
    "KaggleReward",
    "ClassificationReward",
    "RegressionReward",
    # Datasets
    "DatasetConverter",
    # Config
    "VerlConfigBuilder",
    # Utils
    "TraceCollector",
    "Evaluator",
]
