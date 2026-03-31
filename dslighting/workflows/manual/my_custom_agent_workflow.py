"""
My Custom Agent Workflow - 内置自定义 Agent

这个 workflow 展示了如何在 DSLighting 项目内创建自定义 Agent
可以像 aide, data_interpreter 一样使用
"""

from dslighting.workflows.base import BaseWorkflow
from dslighting.state.search.journal import JournalState, Node, MetricValue, maximize_from_lower_is_better
from dslighting.core.data.perception.runtime import DataPerceptionRuntime
from dslighting.prompts.workflows.aide import create_improve_prompt, create_debug_prompt
from dslighting.prompts.common import create_draft_prompt
from dslighting.state.context import summarize_repetitive_logs
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MyCustomAgentWorkflow(BaseWorkflow):
    """
    我的自定义 Agent Workflow

    这是一个完整的 workflow 实现，可以：
    1. 通过 DSLighting.Agent(workflow="my_custom_agent") 使用
    2. 使用所有服务和操作器
    3. 实现自定义的算法逻辑

    算法特点：
    - 智能搜索最佳解决方案
    - 自适应节点选择策略
    - 完整的状态管理
    - 错误历史分析
    """

    def __init__(self, operators: Dict[str, Any], services: Dict[str, Any], agent_config: Dict[str, Any]):
        super().__init__(operators, services, agent_config)

        # 获取所有服务
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.workspace_service = services.get("workspace")
        self.data_perception: Optional[DataPerceptionRuntime] = services.get("data_perception")
        self.state: JournalState = services["state"]

        # 获取所有操作器
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

        logger.info(f"="*80)
        logger.info(f"MyCustomAgentWorkflow 初始化完成")
        logger.info(f"="*80)
        logger.info(f"配置参数:")
        logger.info(f"  - LLM 模型: {self.llm_service.model}")
        logger.info(f"  - LLM 温度: {self.llm_service.temperature}")
        logger.info(f"  - Sandbox 超时: {self.sandbox_service.timeout}s")
        logger.info(f"  - 数据感知: {'已启用' if self.data_perception else '未启用'}")
        logger.info(f"  - 最大迭代次数: {agent_config.get('max_iterations', 5)}")
        logger.info(f"="*80)

    @staticmethod
    def _infer_task_id(output_path: Path, agent_config: Dict[str, Any]) -> Optional[str]:
        for key in ("task_id", "competition_id"):
            value = agent_config.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        name = output_path.stem
        if not name.startswith("submission_"):
            return None

        body = name[len("submission_"):]
        if "_" not in body:
            return None

        maybe_task_id, maybe_suffix = body.rsplit("_", 1)
        hex_chars = set("0123456789abcdefABCDEF")
        if len(maybe_suffix) == 6 and all(char in hex_chars for char in maybe_suffix):
            return maybe_task_id or None
        return None

    async def solve(self, description: str, io_instructions: str, data_dir: Path, output_path: Path) -> None:
        """
        主求解方法

        Args:
            description: 任务描述
            io_instructions: I/O 指令
            data_dir: 数据目录
            output_path: 输出路径
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"MyCustomAgentWorkflow 开始执行")
        logger.info(f"{'='*80}")
        logger.info(f"任务: {description}")
        logger.info(f"数据目录: {data_dir}")
        logger.info(f"输出路径: {output_path}")

        max_iterations = self.agent_config.get("max_iterations", 5)
        inferred_task_id = self._infer_task_id(output_path, self.agent_config)

        # ========== 阶段 1: 数据分析 ==========
        logger.info(f"\n{'─'*80}")
        logger.info(f"阶段 1: 数据分析")
        logger.info(f"{'─'*80}")

        if self.data_perception:
            try:
                data_report = self.data_perception.analyze(
                    data_dir,
                    output_path.name,
                    task_id=inferred_task_id,
                )
                logger.info(f"✓ 数据感知完成")
                logger.debug(f"数据报告摘要:\n{data_report[:500]}...")
            except Exception as e:
                logger.warning(f"数据感知失败: {e}")
                data_report = ""
        else:
            data_report = ""
            logger.info("数据感知未启用，跳过数据分析")

        # 构建任务上下文
        task_context = {
            "goal_and_data": f"{description}\n\n{data_report}",
            "io_instructions": io_instructions
        }
        raw_hints = self.agent_config.get("task_context", {}) if isinstance(self.agent_config, dict) else {}
        if isinstance(raw_hints, dict):
            metric_name = raw_hints.get("metric_name")
            if isinstance(metric_name, str) and metric_name.strip():
                task_context["metric_name"] = metric_name.strip()
            lower_is_better = raw_hints.get("lower_is_better")
            if isinstance(lower_is_better, bool):
                task_context["lower_is_better"] = lower_is_better

        # ========== 阶段 2: 迭代搜索 ==========
        logger.info(f"\n{'─'*80}")
        logger.info(f"阶段 2: 迭代搜索 (最多 {max_iterations} 次)")
        logger.info(f"{'─'*80}")

        for i in range(max_iterations):
            logger.info(f"\n{'='*60}")
            logger.info(f"迭代 {i+1}/{max_iterations}")
            logger.info(f"{'='*60}")

            # 选择要扩展的节点
            parent_node = self._select_node_to_expand()
            if parent_node:
                logger.info(f"父节点: Step #{parent_node.step}")
                logger.info(f"  状态: {'❌ 失败' if parent_node.is_buggy else '✅ 成功'}")
                logger.info(f"  分数: {parent_node.metric}")
            else:
                logger.info(f"首次生成（无父节点）")

            # 生成提示词
            prompt = self._create_prompt(task_context, parent_node)

            # 生成新代码
            logger.info(f"生成代码...")
            plan, code = await self.generate_op(system_prompt=prompt)
            logger.info(f"✓ 代码生成完成")
            logger.debug(f"Plan 摘要: {plan[:150]}...")

            # 创建新节点
            new_node = Node(plan=plan, code=code)
            new_node.task_context = task_context

            # 执行代码
            logger.info(f"执行代码...")
            exec_result = await self.execute_op(code=code, mode="script")
            new_node.absorb_exec_result(exec_result)

            if exec_result.success:
                logger.info(f"✓ 代码执行成功")
                if exec_result.stdout:
                    logger.debug(f"输出摘要:\n{exec_result.stdout[:200]}...")
            else:
                logger.warning(f"✗ 代码执行失败: {new_node.exc_type}")

            # 检查输出文件
            submission_file = self.workspace_service.get_path("sandbox_workdir") / output_path.name
            if exec_result.success and submission_file.exists():
                new_node.is_buggy = False
                logger.info(f"✓ 输出文件已生成: {output_path.name}")
            else:
                new_node.is_buggy = True
                logger.warning(f"✗ 未生成输出文件")

            # 审查结果
            if not new_node.is_buggy:
                logger.info(f"审查代码输出...")
                review_context = {
                    "task": task_context,
                    "code": new_node.code,
                    "output": new_node.term_out
                }
                review = await self.review_op(prompt_context=review_context)
                lower_is_better = task_context.get("lower_is_better")
                if not isinstance(lower_is_better, bool):
                    lower_is_better = review.lower_is_better if isinstance(review.lower_is_better, bool) else None
                new_node.analysis = review.summary
                new_node.metric = MetricValue(
                    value=review.metric_value or 0.0,
                    maximize=maximize_from_lower_is_better(lower_is_better),
                )
                new_node.is_buggy = review.is_buggy
                logger.info(f"✓ 审查完成")
                logger.info(f"  摘要: {review.summary[:100]}...")
                logger.info(f"  评分: {new_node.metric}")
                logger.info(f"  有bug: {new_node.is_buggy}")
            else:
                new_node.analysis = "代码执行失败或未生成输出文件"
                new_node.metric = MetricValue(value=0.0, maximize=True)

            # 添加到状态树
            self.state.append(new_node, parent_node)
            logger.info(f"✓ 节点已添加 (总计 {len(self.state)} 个)")

            # 显示当前最佳
            best = self.state.get_best_node()
            if best:
                logger.info(f"  当前最佳: Step #{best.step}, 分数: {best.metric}")

        # ========== 阶段 3: 生成最终输出 ==========
        logger.info(f"\n{'─'*80}")
        logger.info(f"阶段 3: 生成最终输出")
        logger.info(f"{'─'*80}")

        best_node = self.state.get_best_node()

        if best_node:
            logger.info(f"使用最佳节点: Step #{best_node.step}")
            logger.info(f"  分数: {best_node.metric}")
            logger.debug(f"  Plan: {best_node.plan[:100]}...")

            final_result = await self.execute_op(code=best_node.code, mode="script")

            if final_result.success:
                logger.info(f"✓ 最终输出生成成功！")
                logger.info(f"  输出文件: {output_path}")
            else:
                logger.error(f"✗ 最终输出生成失败: {final_result.stderr}")
        else:
            logger.warning(f"没有找到成功的解决方案")

        logger.info(f"\n{'='*80}")
        logger.info(f"MyCustomAgentWorkflow 执行完成")
        logger.info(f"{'='*80}")
        logger.info(f"统计:")
        logger.info(f"  - 总节点数: {len(self.state)}")
        if best_node:
            logger.info(f"  - 最佳节点: Step #{best_node.step}")
            logger.info(f"  - 最佳分数: {best_node.metric}")
        logger.info(f"{'='*80}\n")

    def _select_node_to_expand(self) -> Optional[Node]:
        """
        选择要扩展的节点

        策略：
        1. 优先扩展成功的、低分的节点（有改进空间）
        2. 如果没有成功的节点，返回最新的失败节点
        3. 如果为空，返回 None（首次生成）
        """
        if len(self.state) == 0:
            return None

        # 获取所有成功的节点
        successful_nodes = [n for n in self.state.nodes.values() if not n.is_buggy]

        if not successful_nodes:
            # 如果没有成功的节点，返回最新的失败节点
            return list(self.state.nodes.values())[-1]

        # 选择分数最低的成功节点（最有改进空间）
        worst_successful = min(successful_nodes, key=lambda n: n.metric.value or float('inf'))
        return worst_successful

    def _create_prompt(self, task_context: Dict[str, str], parent_node: Optional[Node]) -> str:
        """
        根据父节点状态生成合适的提示词

        三种模式：
        1. Draft: 首次生成
        2. Debug: 调试失败节点
        3. Improve: 改进成功节点
        """
        memory_summary = self.state.generate_summary(max_nodes=3)

        if parent_node is None:
            # 首次尝试 - 使用 Draft 提示词
            logger.debug(f"提示词模式: DRAFT (首次生成)")
            return create_draft_prompt(task_context, memory_summary)

        elif parent_node.is_buggy:
            # 调试失败节点 - 使用 Debug 提示词
            logger.debug(f"提示词模式: DEBUG (调试失败)")
            error_history = self._get_error_history(parent_node, max_depth=3)
            return create_debug_prompt(
                task_context,
                parent_node.code,
                error_history,
                previous_plan=parent_node.plan,
                memory_summary=memory_summary
            )

        else:
            # 改进成功节点 - 使用 Improve 提示词
            logger.debug(f"提示词模式: IMPROVE (改进成功)")
            summarized_output = summarize_repetitive_logs(parent_node.term_out)
            return create_improve_prompt(
                task_context,
                memory_summary,
                parent_node.code,
                parent_node.analysis,
                previous_plan=parent_node.plan,
                previous_output=summarized_output
            )

    def _get_error_history(self, node: Node, max_depth: int = 3) -> str:
        """
        获取错误历史

        遍历父节点链，收集所有失败的尝试
        """
        history = []
        current = node
        depth = 0

        while current and current.is_buggy and depth < max_depth:
            entry = (
                f"--- Failure at Step #{current.step} ---\n"
                f"Plan: {current.plan}\n"
                f"Error: {current.exc_type or 'Unknown'}\n"
                f"Output:\n{current.term_out[:300]}..."
            )
            history.append(entry)
            depth += 1
            current = self.state.get_node(current.parent_id) if current.parent_id else None

        if not history:
            return "No error history"

        # 反转以显示时间顺序（最旧的失败在前）
        return "\n".join(reversed(history))
