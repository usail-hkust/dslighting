"""
Data Interpreter Training Agent

A preset training agent wrapper for the Data Interpreter workflow.
"""
from dslighting.training.agents.presets.preset_factory import (
    DataInterpreterTrainingAgent as DataInterpreterTrainingAgentImpl,
    create_preset_agent,
)

# For backward compatibility, keep the class but use factory implementation
DataInterpreterTrainingAgent = DataInterpreterTrainingAgentImpl

__all__ = ["DataInterpreterTrainingAgent", "create_preset_agent"]
