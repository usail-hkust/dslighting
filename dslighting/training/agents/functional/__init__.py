"""
DSLighting Training Agents - Functional

函数式 Agent（使用 @rollout 装饰器）
"""
from dslighting.training.agents.functional.workflow_agent import (
    train_aide_agent,
    train_autokaggle_agent,
    train_data_interpreter_agent,
)

__all__ = [
    "train_aide_agent",
    "train_autokaggle_agent",
    "train_data_interpreter_agent",
]
