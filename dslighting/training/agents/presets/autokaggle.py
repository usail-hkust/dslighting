"""
AutoKaggle Training Agent
"""
from dslighting.training.agents.lit_ds_agent import LitDSAgent
from typing import Dict, Any


class AutoKaggleTrainingAgent(LitDSAgent):
    """
    AutoKaggle Workflow 训练 Agent
    """

    def __init__(
        self,
        workflow_config: Dict[str, Any] = None,
        reward_evaluator = None,
        max_steps: int = 100,
    ):
        super().__init__(
            workflow_name="autokaggle",
            workflow_config=workflow_config or {},
            reward_evaluator=reward_evaluator,
            max_steps=max_steps,
        )


__all__ = ["AutoKaggleTrainingAgent"]
