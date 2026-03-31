"""
DSLighting Training Agent - wraps DSLighting workflows as Agent-Lightning LitAgents.
"""
import asyncio
from typing import Any, Dict

try:
    import agentlightning as agl
except ImportError as exc:
    raise ImportError(
        "LitDSAgent requires optional dependency 'agentlightning'. "
        "Install it to use dslighting.training agents."
    ) from exc

from dslighting.core.application.agent_app_service import AgentAppService
from dslighting.training.rewards.base import RewardEvaluator


class LitDSAgent(agl.LitAgent[Dict[str, Any]]):
    """
    Wraps a DSLighting workflow as an Agent-Lightning training agent.

    Parameters
    ----------
    workflow_name : str
        DSLighting workflow name (e.g., "aide", "autokaggle", "data_interpreter").
    workflow_config : Dict[str, Any]
        Workflow init kwargs forwarded to AgentAppService (e.g., max_iterations).
    reward_evaluator : RewardEvaluator
        Reward evaluator used to score the workflow result.
    max_steps : int, default=100
        Maximum execution steps passed to the workflow.
    """

    def __init__(
        self,
        workflow_name: str,
        workflow_config: Dict[str, Any],
        reward_evaluator: RewardEvaluator,
        max_steps: int = 100,
    ):
        super().__init__()
        self.workflow_name = workflow_name
        self.workflow_config = workflow_config
        self.reward_evaluator = reward_evaluator
        self.max_steps = max_steps

    def rollout(
        self,
        task: Dict[str, Any],
        resources: agl.NamedResources,
        rollout: agl.Rollout,
    ) -> float:
        """
        Execute a workflow rollout for the given task.

        Parameters
        ----------
        task : Dict[str, Any]
            Task dict with keys: task_id, data_dir, description (optional),
            output (optional), metadata (optional).
        resources : agl.NamedResources
            Training resources; expects "main_llm": agl.LLM.
        rollout : agl.Rollout
            Rollout context.

        Returns
        -------
        float
            Final reward value (0.0 on failure).
        """
        llm: agl.LLM = resources["main_llm"]

        agl.emit_message(
            f"[{self.workflow_name}] Starting rollout for task {task.get('task_id')}"
        )

        init_kwargs = {**self.workflow_config, "max_steps": self.max_steps}

        service = AgentAppService(
            workflow_name=self.workflow_name,
            model=llm.model,
            api_key=llm.api_key or None,
            api_keys=None,
            api_base=llm.endpoint or None,
            provider=None,
            temperature=llm.sampling_parameters.get("temperature", 0.7),
            timeout=None,
            keep_workspace=False,
            sandbox_backend=None,
            sandbox_backend_type=None,
            sandbox_timeout=None,
            sandbox_api_key=None,
            init_kwargs=init_kwargs,
        )

        try:
            result = asyncio.run(
                service.run(
                    task_id=task.get("task_id"),
                    data=task["data_dir"],
                    task=task.get("description", ""),
                    output=task.get("output", "submission.csv"),
                    kwargs=task.get("metadata", {}),
                )
            )

            reward = self.reward_evaluator.evaluate(result=result, task=task)

            agl.emit_object(
                {
                    "workflow": self.workflow_name,
                    "task_id": task.get("task_id"),
                    "success": result.success,
                    "score": result.score,
                    "reward": reward,
                }
            )

            return reward

        except Exception as e:
            agl.emit_exception(e)
            agl.emit_message(f"[{self.workflow_name}] Rollout failed: {e}")
            return 0.0


__all__ = ["LitDSAgent"]
