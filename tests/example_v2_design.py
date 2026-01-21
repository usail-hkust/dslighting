"""
DSLiginting 2.0 新设计 - 完整使用示例

展示如何使用重新设计的 DSLighting 2.0：
1. 标准化 Prompts（JSON 格式）
2. 标准 Agent 模式
3. 清晰的扩展方式

Author: DSLighting Team
Date: 2026-01-18
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# 第 1 部分：使用标准 Prompts
# ============================================================================

print("\n" + "="*70)
print("第 1 部分：使用标准 Prompts")
print("="*70)

from dslighting import (
    BaseAgent,
    create_modeling_prompt,
    create_eda_prompt,
    create_debug_prompt,
)

class Example1_UsingStandardPrompts(BaseAgent):
    """
    示例 1：使用 DSLighting 的标准 Prompts

    优点：
    - 无需从头写 prompt
    - 统一的格式（JSON）
    - 易于理解和修改
    """

    async def solve(self, description, io_instructions, data_dir, output_path):
        print("\n📝 使用标准建模 Prompt...")

        # 方式 1: 使用标准 modeling prompt
        prompt = create_modeling_prompt(
            task_type="regression",
            data_description=f"数据位于: {data_dir}",
            target_variable=io_instructions,
            requirements=[
                "使用随机森林或 XGBoost",
                "打印交叉验证分数",
                "保存预测到 submission.csv"
            ]
        )

        print(f"生成的 Prompt:\n{'-'*70}")
        print(prompt[:500] + "...")
        print(f"{'-'*70}\n")

        # 生成代码
        plan, code = await self.generate_op(system_prompt=prompt)

        # 执行代码
        result = await self.execute_op(code=code, mode="script")

        return result


# ============================================================================
# 第 2 部分：继承标准 Agent
# ============================================================================

print("\n" + "="*70)
print("第 2 部分：继承标准 Agent")
print("="*70)

from dslighting import IterativeAgent

class Example2_CustomIterativeAgent(IterativeAgent):
    """
    示例 2：继承标准 IterativeAgent

    优点：
    - 无需从头实现迭代逻辑
    - 只需覆盖关键方法
    - 自动获得状态管理
    """

    def _create_iteration_prompt(self, description, io_instructions, data_dir, output_path, iteration, best_score):
        """
        覆盖：自定义迭代 prompt 生成

        这是最常见的扩展点。
        """

        if iteration == 0:
            # 首次：简单直接
            return f"""
任务: {description}
数据目录: {data_dir}
输出文件: {output_path}

请提供一个初始解决方案。
使用简单但有效的方法。
"""
        else:
            # 后续：改进策略
            return f"""
任务: {description}
当前迭代: {iteration + 1}
当前最佳分数: {best_score:.4f}

请改进解决方案。

建议方向：
1. 尝试不同的算法（如 XGBoost, LightGBM, CatBoost）
2. 改进特征工程
3. 调整超参数
4. 使用集成方法

重点关注：
- 特征选择和变换
- 模型参数调优
- 交叉验证策略
"""


# ============================================================================
# 第 3 部分：自定义 Prompt（使用标准格式）
# ============================================================================

print("\n" + "="*70)
print("第 3 部分：自定义 Prompt（使用标准格式）")
print("="*70)

from dslighting.prompts import create_prompt_template, get_common_guidelines

def create_my_custom_prompt(task_description: str, data_info: str, focus_area: str) -> str:
    """
    创建自定义 Prompt

    使用 DSLighting 的标准格式，确保一致性。
    """

    prompt_dict = {
        "Role": "You are an expert Data Scientist and ML Engineer.",
        "Task": task_description,
        "Data Information": data_info,
        "Focus Area": focus_area,
        "Instructions": {
            "Goal": "Provide the best possible solution",
            "Approach": [
                f"Focus on {focus_area}",
                "Use best practices",
                "Ensure code is production-ready"
            ],
            **get_common_guidelines()  # 复用标准指南
        }
    }

    return create_prompt_template(prompt_dict)


class Example3_CustomPrompt(BaseAgent):
    """示例 3：使用自定义 Prompt（但遵循标准格式）"""

    async def solve(self, description, io_instructions, data_dir, output_path):
        print("\n📝 使用自定义 Prompt（标准格式）...")

        # 使用自定义 prompt 函数
        prompt = create_my_custom_prompt(
            task_description=description,
            data_info=str(data_dir),
            focus_area="特征工程和模型优化"
        )

        print(f"自定义 Prompt:\n{'-'*70}")
        print(prompt[:500] + "...")
        print(f"{'-'*70}\n")

        # 生成代码
        plan, code = await self.generate_op(system_prompt=prompt)

        # 执行代码
        result = await self.execute_op(code=code, mode="script")

        return result


# ============================================================================
# 第 4 部分：完整的端到端示例
# ============================================================================

print("\n" + "="*70)
print("第 4 部分：完整的端到端示例")
print("="*70)

class MySmartAgent(IterativeAgent):
    """
    完整示例：智能 Agent

    结合：
    1. 标准 Prompt 格式
    2. 继承标准 Agent
    3. 自定义策略
    """

    def _create_iteration_prompt(self, description, io_instructions, data_dir, output_path, iteration, best_score):
        """自定义迭代策略"""

        if iteration == 0:
            # 第 1 次：使用标准 EDA + 建模
            return create_modeling_prompt(
                task_type="regression",
                data_description=f"数据位于: {data_dir}",
                target_variable=io_instructions,
                requirements=[
                    "首先进行探索性数据分析",
                    "然后建立基线模型",
                    "打印关键指标"
                ]
            )
        elif iteration == 1:
            # 第 2 次：特征工程
            return f"""
任务: {description}
当前最佳分数: {best_score:.4f}

请专注于**特征工程**：
1. 创建交互特征
2. 特征变换（log, sqrt 等）
3. 特征选择
4. 特征缩放

使用更好的特征重新训练模型。
"""
        elif iteration == 2:
            # 第 3 次：模型调优
            return f"""
任务: {description}
当前最佳分数: {best_score:.4f}

请专注于**模型调优**：
1. 尝试不同的算法（XGBoost, LightGBM, CatBoost）
2. 超参数调优（使用网格搜索或随机搜索）
3. 交叉验证
4. 集成方法

目标是显著提升模型性能。
"""
        else:
            # 后续：综合优化
            return f"""
任务: {description}
当前迭代: {iteration + 1}
当前最佳分数: {best_score:.4f}

请进行**综合优化**：
1. 结合之前的最佳实践
2. 尝试集成方法（bagging, boosting, stacking）
3. 精细调整
4. 确保模型泛化能力

必须显著超越当前最佳分数 {best_score:.4f}
"""

    async def _evaluate_result(self, description, code, result):
        """自定义评估逻辑"""

        # 从输出中提取分数
        import re

        # 尝试多种常见的分数格式
        patterns = [
            r"Score[:\s]+([0-9.]+)",
            r"RMSE[:\s]+([0-9.]+)",
            r"R²[:\s]+([0-9.]+)",
            r"R2[:\s]+([0-9.]+)",
            r"accuracy[:\s]+([0-9.]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, result.stdout, re.IGNORECASE)
            if match:
                score_str = match.group(1)
                try:
                    score = float(score_str)

                    # 对于 RMSE，越小越好，需要转换
                    if "RMSE" in pattern or "rmse" in pattern:
                        score = -score  # 转换为越大越好

                    print(f"✓ 提取到分数: {score:.4f}")
                    return score
                except ValueError:
                    continue

        # 如果找不到，使用 review operator
        print("⚠ 无法从输出提取分数，使用 review operator")
        review = await self.review_op(prompt_context={
            "task": description,
            "code": code,
            "output": result.stdout
        })

        return review.metric_value or 0.0


# ============================================================================
# 第 5 部分：运行示例
# ============================================================================

async def run_examples():
    """运行所有示例"""

    from dslighting import (
        LLMService,
        SandboxService,
        WorkspaceService,
        JournalState,
        GenerateCodeAndPlanOperator,
        ExecuteAndTestOperator,
        ReviewOperator,
    )

    print("\n" + "="*70)
    print("DSLiginting 2.0 新设计 - 完整示例")
    print("="*70)

    # 创建服务
    workspace = WorkspaceService(run_name="v2_design_demo")
    llm_service = LLMService(model="gpt-4o-mini")  # 使用更便宜的模型
    sandbox_service = SandboxService(workspace=workspace, timeout=300)
    state = JournalState()

    # 创建操作器
    operators = {
        "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
        "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
        "review": ReviewOperator(llm_service=llm_service),
    }

    # 创建服务字典
    services = {
        "llm": llm_service,
        "sandbox": sandbox_service,
        "workspace": workspace,
        "state": state,
    }

    # 配置
    agent_config = {
        "max_iterations": 3,
        "early_stopping": True,
        "improvement_threshold": 0.01
    }

    # 数据目录
    data_dir = Path("/Users/liufan/Applications/Github/dslighting/datasets/bike-sharing-demand")

    # ========================================================================
    # 示例 1：使用标准 Prompts
    # ========================================================================

    print("\n" + "="*70)
    print("运行示例 1：使用标准 Prompts")
    print("="*70)

    agent1 = Example1_UsingStandardPrompts(operators, services, {})

    result1 = await agent1.solve(
        description="预测 bike sharing demand",
        io_instructions="count",
        data_dir=data_dir,
        output_path=Path("submission_example1.csv")
    )

    print(f"\n示例 1 结果: {'✓ 成功' if result1.success else '✗ 失败'}")

    # ========================================================================
    # 示例 2：继承标准 Agent
    # ========================================================================

    print("\n" + "="*70)
    print("运行示例 2：继承标准 Agent")
    print("="*70)

    agent2 = Example2_CustomIterativeAgent(operators, services, agent_config)

    result2 = await agent2.solve(
        description="预测 bike sharing demand",
        io_instructions="count",
        data_dir=data_dir,
        output_path=Path("submission_example2.csv")
    )

    print(f"\n示例 2 结果: {'✓ 成功' if result2.success else '✗ 失败'}")

    # ========================================================================
    # 示例 3：自定义 Prompt
    # ========================================================================

    print("\n" + "="*70)
    print("运行示例 3：自定义 Prompt")
    print("="*70)

    agent3 = Example3_CustomPrompt(operators, services, {})

    result3 = await agent3.solve(
        description="预测 bike sharing demand",
        io_instructions="count",
        data_dir=data_dir,
        output_path=Path("submission_example3.csv")
    )

    print(f"\n示例 3 结果: {'✓ 成功' if result3.success else '✗ 失败'}")

    # ========================================================================
    # 示例 4：完整的智能 Agent
    # ========================================================================

    print("\n" + "="*70)
    print("运行示例 4：完整的智能 Agent")
    print("="*70)

    agent4 = MySmartAgent(operators, services, agent_config)

    result4 = await agent4.solve(
        description="预测 bike sharing demand，目标是获得最佳性能",
        io_instructions="count",
        data_dir=data_dir,
        output_path=Path("submission_example4.csv")
    )

    print(f"\n示例 4 结果: {'✓ 成功' if result4.success else '✗ 失败'}")

    # ========================================================================
    # 总结
    # ========================================================================

    print("\n" + "="*70)
    print("所有示例运行完成！")
    print("="*70)

    print("""
总结：
1. ✓ 使用标准 Prompts - 简单直接
2. ✓ 继承标准 Agent - 快速开发
3. ✓ 自定义 Prompt - 灵活扩展
4. ✓ 完整的智能 Agent - 生产就绪

DSLiginting 2.0 新设计的优势：
- 清晰的层次结构
- 标准化的组件
- 易于扩展和自定义
- 完全基于 DSAT
    """)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          DSLiginting 2.0 新设计 - 完整使用示例                ║
║                                                                ║
║  展示：                                                        ║
║  1. 标准化 Prompts（JSON 格式）                               ║
║  2. 标准 Agent 模式（Simple, Iterative）                      ║
║  3. 清晰的扩展方式                                            ║
║  4. 完全基于 DSAT                                             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # 运行示例
    asyncio.run(run_examples())
