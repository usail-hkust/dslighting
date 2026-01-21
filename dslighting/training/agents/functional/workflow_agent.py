"""
函数式 Workflow Agent - 使用 @rollout 装饰器
"""
import agentlightning as agl
from typing import Dict
from dslighting.training.rewards.base import RewardEvaluator


@agl.rollout
def train_aide_agent(
    task: Dict[str, Any],
    llm: agl.LLM,
    rollout: agl.Rollout,
    reward_evaluator: RewardEvaluator,
) -> float:
    """
    使用 AIDE workflow 训练的函数式 Agent

    Parameters
    ----------
    task : Dict[str, Any]
        任务字典
    llm : agl.LLM
        注入的 LLM 资源
    rollout : agl.Rollout
        Rollout 上下文
    reward_evaluator : RewardEvaluator
        奖励评估器

    Returns
    -------
    float
        最终奖励
    """
    from dslighting import Agent

    agl.emit_message(f"[AIDE] Starting training rollout for {task['task_id']}")

    # 使用 DSLighting Agent API
    agent = Agent(
        workflow="aide",
        model=llm.model,
        api_base=llm.endpoint,
        api_key=llm.api_key,
    )

    # 运行 agent
    result = agent.run(task_id=task["task_id"])

    # 计算奖励
    reward = reward_evaluator.evaluate(result, task)

    # 发送 trace
    agl.emit_object({
        "workflow": "aide",
        "score": result.score,
        "reward": reward,
    })

    return reward


@agl.rollout
def train_autokaggle_agent(
    task: Dict[str, Any],
    llm: agl.LLM,
    rollout: agl.Rollout,
    reward_evaluator: RewardEvaluator,
) -> float:
    """使用 AutoKaggle workflow 训练的函数式 Agent"""
    from dslighting import Agent

    agl.emit_message(f"[AutoKaggle] Starting training rollout for {task['task_id']}")

    agent = Agent(
        workflow="autokaggle",
        model=llm.model,
        api_base=llm.endpoint,
        api_key=llm.api_key,
    )

    result = agent.run(task_id=task["task_id"])
    reward = reward_evaluator.evaluate(result, task)

    agl.emit_object({
        "workflow": "autokaggle",
        "score": result.score,
        "reward": reward,
    })

    return reward


@agl.rollout
def train_data_interpreter_agent(
    task: Dict[str, Any],
    llm: agl.LLM,
    rollout: agl.Rollout,
    reward_evaluator: RewardEvaluator,
) -> float:
    """使用 Data Interpreter workflow 训练的函数式 Agent"""
    from dslighting import Agent

    agl.emit_message(f"[DataInterpreter] Starting training rollout for {task['task_id']}")

    agent = Agent(
        workflow="data_interpreter",
        model=llm.model,
        api_base=llm.endpoint,
        api_key=llm.api_key,
    )

    result = agent.run(task_id=task["task_id"])
    reward = reward_evaluator.evaluate(result, task)

    agl.emit_object({
        "workflow": "data_interpreter",
        "score": result.score,
        "reward": reward,
    })

    return reward


__all__ = [
    "train_aide_agent",
    "train_autokaggle_agent",
    "train_data_interpreter_agent",
]
