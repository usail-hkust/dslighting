"""
AutoKaggle Training Agent

A preset training agent wrapper for the AutoKaggle workflow.
"""
from dslighting.training.agents.presets.preset_factory import (
    AutoKaggleTrainingAgent as AutoKaggleTrainingAgentImpl,
    create_preset_agent,
)

# For backward compatibility, keep the class but use factory implementation
AutoKaggleTrainingAgent = AutoKaggleTrainingAgentImpl

__all__ = ["AutoKaggleTrainingAgent", "create_preset_agent"]
