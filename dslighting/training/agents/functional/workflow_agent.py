"""
Functional Workflow Agents - Using @rollout decorator

Provides functional agent implementations for different workflows.
"""
import agentlightning as agl
from typing import Any, Callable, Dict, Optional

from dslighting.training.rewards.base import RewardEvaluator


def _create_workflow_agent(
    workflow_name: str,
    emit_prefix: str,
) -> Callable[..., float]:
    """
    Factory function to create workflow agent functions.

    Generates a parameterized rollout function for a specific workflow.

    Parameters
    ----------
    workflow_name : str
        Name of the workflow (e.g., "aide", "autokaggle", "data_interpreter").
    emit_prefix : str
        Prefix for log messages (e.g., "AIDE", "AutoKaggle").

    Returns
    -------
    Callable
        A rollout-decorated function for training with the specified workflow.
    """
    # Get display name for messages
    display_name = workflow_name.replace("_", " ").title()

    @agl.rollout
    def _agent_func(
        task: Dict[str, Any],
        llm: agl.LLM,
        rollout: agl.Rollout,
        reward_evaluator: RewardEvaluator,
    ) -> float:
        """
        Functional agent for {display_name} workflow training.

        Parameters
        ----------
        task : Dict[str, Any]
            Task dictionary containing task_id and data information.
        llm : agl.LLM
            Injected LLM resource.
        rollout : agl.Rollout
            Rollout context.
        reward_evaluator : RewardEvaluator
            Reward evaluator for computing training rewards.

        Returns
        -------
        float
            Final reward value.
        """
        from dslighting import Agent

        agl.emit_message(f"[{emit_prefix}] Starting training rollout for {task['task_id']}")

        # Create DSLighting Agent API instance
        agent = Agent(
            workflow=workflow_name,
            model=llm.model,
            api_base=llm.endpoint,
            api_key=llm.api_key,
        )

        # Run agent on task
        result = agent.run(task_id=task["task_id"])

        # Compute reward
        reward = reward_evaluator.evaluate(result, task)

        # Emit trace data
        agl.emit_object({
            "workflow": workflow_name,
            "score": result.score,
            "reward": reward,
        })

        return reward

    # Set function name for better debugging
    func_name = f"train_{workflow_name}_agent"
    _agent_func.__name__ = func_name

    return _agent_func


# Create functional agents for each workflow
# These agents have nearly identical code, generated via factory function
train_aide_agent = _create_workflow_agent("aide", "AIDE")
train_autokaggle_agent = _create_workflow_agent("autokaggle", "AutoKaggle")
train_data_interpreter_agent = _create_workflow_agent("data_interpreter", "DataInterpreter")


__all__ = [
    "train_aide_agent",
    "train_autokaggle_agent",
    "train_data_interpreter_agent",
]
