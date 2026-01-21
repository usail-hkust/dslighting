"""
DSLighting Training Agent - 包装 DSAT Workflows

将 DSAT workflows 包装为 Agent-Lightning 的 LitAgent
"""
import agentlightning as agl
from typing import Any, Dict

try:
    from dsat.workflows.factory import get_workflow
except ImportError:
    get_workflow = None

from dslighting.training.rewards.base import RewardEvaluator


class LitDSAgent(agl.LitAgent[Dict[str, Any]]):
    """
    将 DSAT workflow 包装为 Agent-Lightning 训练 Agent

    Parameters
    ----------
    workflow_name : str
        DSAT workflow 名称 (e.g., "aide", "autokaggle", "data_interpreter")
    workflow_config : Dict[str, Any]
        Workflow 配置参数
    reward_evaluator : RewardEvaluator
        奖励评估器
    max_steps : int, default=100
        最大执行步数
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
        rollout: agl.Rollout
    ) -> float:
        """
        执行 workflow rollout

        Parameters
        ----------
        task : Dict[str, Any]
            任务字典，包含:
            - task_id: str
            - data_dir: str
            - metadata: dict
        resources : agl.NamedResources
            训练资源，包含:
            - "main_llm": agl.LLM
        rollout : agl.Rollout
            Rollout 上下文

        Returns
        -------
        float
            最终奖励值
        """
        # 1. 从 resources 获取 LLM
        llm: agl.LLM = resources["main_llm"]

        # 2. 发送消息：开始 rollout
        agl.emit_message(f"[{self.workflow_name}] Starting rollout for task {task.get('task_id')}")

        if get_workflow is None:
            agl.emit_exception(ImportError("DSAT not available"))
            return 0.0

        # 3. 更新 workflow 配置使用训练 LLM
        workflow_config = self.workflow_config.copy()
        workflow_config.update({
            "llm_config": {
                "model": llm.model,
                "api_base": llm.endpoint,
                "api_key": llm.api_key or "dummy-key",
                "temperature": llm.sampling_parameters.get("temperature", 0.7),
            },
            "max_steps": self.max_steps,
        })

        # 4. 创建 DSAT workflow
        workflow = get_workflow(
            workflow_name=self.workflow_name,
            config=workflow_config
        )

        # 5. 执行 workflow
        try:
            result = workflow.run(
                task_id=task["task_id"],
                data_dir=task["data_dir"],
            )

            # 6. 发送中间奖励（如果有）
            if hasattr(result, "intermediate_scores"):
                for step, score in enumerate(result.intermediate_scores):
                    agl.emit_reward(score)

            # 7. 使用 reward_evaluator 计算最终奖励
            reward = self.reward_evaluator.evaluate(
                result=result,
                task=task,
            )

            # 8. 发送结构化数据
            agl.emit_object({
                "workflow": self.workflow_name,
                "task_id": task["task_id"],
                "final_score": result.score if hasattr(result, "score") else None,
                "steps_taken": len(result.history) if hasattr(result, "history") else 0,
                "reward": reward,
            })

            return reward

        except Exception as e:
            # 捕获异常并记录
            agl.emit_exception(e)
            agl.emit_message(f"[{self.workflow_name}] Rollout failed: {str(e)}")
            return 0.0  # 失败返回零奖励


__all__ = ["LitDSAgent"]
