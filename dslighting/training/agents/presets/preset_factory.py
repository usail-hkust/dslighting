"""
Preset Training Agent Factory

Factory functions for creating preset training agents for different workflows.
"""
from typing import Any, Dict, Optional, Type

from dslighting.training.agents.lit_ds_agent import LitDSAgent


def create_preset_agent(
    workflow_name: str,
    workflow_config: Optional[Dict[str, Any]] = None,
    reward_evaluator = None,
    max_steps: int = 50,
) -> LitDSAgent:
    """
    Factory function to create a preset training agent.

    Creates a LitDSAgent instance configured for a specific workflow.

    Parameters
    ----------
    workflow_name : str
        Name of the workflow (e.g., "aide", "autokaggle", "data_interpreter").
    workflow_config : Optional[Dict[str, Any]], optional
        Configuration dictionary for the workflow.
    reward_evaluator : optional
        Reward evaluator instance for computing training rewards.
    max_steps : int, optional
        Maximum number of workflow steps. Defaults to 50.

    Returns
    -------
    LitDSAgent
        Configured training agent instance.
    """
    return LitDSAgent(
        workflow_name=workflow_name,
        workflow_config=workflow_config or {},
        reward_evaluator=reward_evaluator,
        max_steps=max_steps,
    )


# Preset agent class factory for backward compatibility
def _create_agent_class(workflow_name: str, default_max_steps: int = 50) -> Type[LitDSAgent]:
    """
    Factory function to create preset agent classes dynamically.

    Generates a LitDSAgent subclass configured for a specific workflow.

    Parameters
    ----------
    workflow_name : str
        Name of the workflow.
    default_max_steps : int, optional
        Default maximum number of workflow steps.

    Returns
    -------
    Type[LitDSAgent]
        Preset agent class.
    """

    class PresetAgent(LitDSAgent):
        """
        Preset training agent for {workflow_name} workflow.

        A lightweight wrapper around LitDSAgent that configures
        the {workflow_name} workflow for agent training scenarios.

        Parameters
        ----------
        workflow_config : Optional[Dict[str, Any]], optional
            Configuration dictionary for the workflow. Defaults to None.
        reward_evaluator : optional
            Reward evaluator instance for computing training rewards.
        max_steps : int, optional
            Maximum number of workflow steps. Defaults to {default_max_steps}.
        """

        def __init__(
            self,
            workflow_config: Optional[Dict[str, Any]] = None,
            reward_evaluator = None,
            max_steps: int = default_max_steps,
        ):
            super().__init__(
                workflow_name=workflow_name,
                workflow_config=workflow_config or {},
                reward_evaluator=reward_evaluator,
                max_steps=max_steps,
            )

    # Set class name and docstring
    class_name = f"{workflow_name.title().replace('_', '')}TrainingAgent"
    PresetAgent.__name__ = class_name
    PresetAgent.__doc__ = PresetAgent.__doc__.format(
        workflow_name=workflow_name,
        default_max_steps=default_max_steps,
    )

    return PresetAgent


# Preset agent classes (created via factory for code reuse)
AIDETrainingAgent = _create_agent_class("aide", default_max_steps=50)
AutoKaggleTrainingAgent = _create_agent_class("autokaggle", default_max_steps=100)
DataInterpreterTrainingAgent = _create_agent_class("data_interpreter", default_max_steps=50)

__all__ = [
    "create_preset_agent",
    "AIDETrainingAgent",
    "AutoKaggleTrainingAgent",
    "DataInterpreterTrainingAgent",
]
