"""
DSLighting Training Agents - Presets

Preset training agent wrappers for different workflows.
"""
from dslighting.training.agents.presets.aide import (
    AIDETrainingAgent,
    create_preset_agent,
)
from dslighting.training.agents.presets.autokaggle import (
    AutoKaggleTrainingAgent,
    create_preset_agent as create_autokaggle_agent,
)
from dslighting.training.agents.presets.data_interpreter import (
    DataInterpreterTrainingAgent,
    create_preset_agent as create_data_interpreter_agent,
)

__all__ = [
    "AIDETrainingAgent",
    "AutoKaggleTrainingAgent",
    "DataInterpreterTrainingAgent",
    "create_preset_agent",
]
