"""
AIDE Training Agent

A preset training agent wrapper for the AIDE workflow.
"""
from dslighting.training.agents.presets.preset_factory import (
    AIDETrainingAgent as AIDETrainingAgentImpl,
    create_preset_agent,
)

# For backward compatibility, keep the class but use factory implementation
AIDETrainingAgent = AIDETrainingAgentImpl

__all__ = ["AIDETrainingAgent", "create_preset_agent"]
