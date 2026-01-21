"""
示例: 使用自定义 Operator 的 Agent

这是一个完整的示例，展示如何在自定义 Agent 中使用自定义 Operator。
"""
import logging
from pathlib import Path
from typing import Dict, Any

from dslighting.agents import BaseAgent
from dslighting.services import LLMService, SandboxService
from dslighting.operators.custom import TextAnalysisOperator

logger = logging.getLogger(__name__)


class ExampleAgentWithCustomOperator(BaseAgent):
    """
    示例 Agent - 使用自定义 Operator

    功能：
    1. 使用自定义 TextAnalysisOperator 分析任务
    2. 使用标准 operators 生成和执行代码
    """

    def __init__(
        self,
        operators: Dict[str, Any],
        services: Dict[str, Any],
        agent_config: Dict[str, Any],
    ):
        """
        初始化

        Args:
            operators: 算子字典（包含自定义 operators）
            services: 服务字典
            agent_config: Agent 配置
        """
        super().__init__(operators, services, agent_config)

        # ========== 获取标准 Operators ==========
        self.execute_op = operators["execute"]
        self.generate_op = operators["generate"]

        # ========== 获取自定义 Operators ==========
        # 这是我们在 custom/example_operator.py 中定义的
        self.text_analysis_op = operators["text_analysis"]

        # ========== 获取 Services ==========
        self.llm_service: LLMService = services["llm"]
        self.sandbox_service: SandboxService = services["sandbox"]

        # ========== 获取配置 ==========
        self.max_iterations = agent_config.get("max_iterations", 5)

        logger.info(f"[{self.__class__.__name__}] Initialized with custom operator")

    async def solve(
        self,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path
    ) -> None:
        """
        核心求解方法

        Args:
            description: 任务描述
            io_instructions: 输入输出说明
            data_dir: 数据目录
            output_path: 输出路径
        """
        logger.info(f"[{self.__class__.__name__}] Starting task")
        logger.info(f"  Description: {description[:100]}...")

        # ========== 步骤 1: 使用自定义 Operator 分析任务 ==========
        logger.info("\n--- Step 1: Analyzing task with custom operator ---")
        analysis = await self.text_analysis_op(
            text=description,
            analysis_type="summary"
        )
        logger.info(f"Task summary: {analysis['raw_response'][:200]}...")

        # ========== 步骤 2: 使用标准 Operator 生成代码 ==========
        logger.info("\n--- Step 2: Generating code ---")
        prompt = f"""
Task: {description}

Instructions:
{io_instructions}

Data directory: {data_dir}

Please generate Python code to solve this task.
"""

        plan, code = await self.generate_op(system_prompt=prompt)
        logger.info(f"Generated plan: {plan[:100]}...")
        logger.info(f"Generated code: {len(code)} characters")

        # ========== 步骤 3: 使用标准 Operator 执行代码 ==========
        logger.info("\n--- Step 3: Executing code ---")
        exec_result = await self.execute_op(code=code, mode="script")

        if exec_result.success:
            logger.info("✓ Code executed successfully")
            logger.info(f"Output: {exec_result.stdout[:200]}...")

            # ========== 步骤 4: 保存结果 ==========
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(exec_result.stdout)

            logger.info(f"✓ Result saved to {output_path}")

        else:
            logger.error(f"✗ Code execution failed: {exec_result.stderr}")
            raise RuntimeError(f"Execution failed: {exec_result.stderr}")

        logger.info(f"\n[{self.__class__.__name__}] Task completed successfully")


# 使用示例
"""
# 配置
from dslighting.services import LLMService, SandboxService
from dslighting.operators import GenerateCodeAndPlanOperator, ExecuteAndTestOperator
from dslighting.operators.custom import TextAnalysisOperator
from dslighting.state import JournalState

# 1. 创建 services
services = {
    "llm": LLMService(model="gpt-4o"),
    "sandbox": SandboxService(),
    "state": JournalState(),
    "workspace": None,
}

# 2. 创建 operators
operators = {
    "generate": GenerateCodeAndPlanOperator(llm_service=services["llm"]),
    "execute": ExecuteAndTestOperator(sandbox_service=services["sandbox"]),
    "text_analysis": TextAnalysisOperator(llm_service=services["llm"]),  # 自定义 operator
}

# 3. 创建 agent config
agent_config = {
    "max_iterations": 5,
}

# 4. 创建 agent
agent = ExampleAgentWithCustomOperator(operators, services, agent_config)

# 5. 运行
import asyncio

async def main():
    await agent.solve(
        description="分析数据并生成报告",
        io_instructions="读取 train.csv，生成 report.txt",
        data_dir=Path("./data"),
        output_path=Path("./output/result.txt")
    )

asyncio.run(main())
"""
