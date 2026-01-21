"""
在 bike-sharing-demand 上运行自定义 Agent

完整示例：展示如何基于 DSAT 创建自定义 Agent
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from pathlib import Path
import sys

# 导入自定义 Agent
sys.path.insert(0, '/Users/liufan/Applications/Github/test_pip_dslighting')
from my_agents.intelligent_search_agent import IntelligentSearchAgent

# 导入 DSAT 组件
from dsat.services.workspace import WorkspaceService
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.services.data_analyzer import DataAnalyzer
from dsat.services.states.journal import JournalState
from dsat.operators.llm_basic import GenerateCodeAndPlanOperator, ReviewOperator
from dsat.operators.code import ExecuteAndTestOperator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """主函数"""

    print("\n" + "="*80)
    print("在 bike-sharing-demand 上运行自定义 DSAT Agent")
    print("="*80)

    # ========== 步骤 1: 创建 DSAT 服务 ==========
    print("\n步骤 1: 创建 DSAT 服务")
    print("-"*80)

    workspace = WorkspaceService(
        run_name="intelligent_search_bike_test",
        base_dir="/Users/liufan/Applications/Github/test_pip_dslighting/dsat_runs"
    )

    llm_service = LLMService(
        model="gpt-4o",
        temperature=0.7
    )

    sandbox_service = SandboxService(
        workspace=workspace,
        timeout=300  # 5 分钟
    )

    data_analyzer = DataAnalyzer()
    state = JournalState()

    print("✓ WorkspaceService 创建成功")
    print(f"  路径: {workspace.run_dir}")
    print("✓ LLMService 创建成功")
    print(f"  模型: {llm_service.model}")
    print(f"  温度: {llm_service.temperature}")
    print("✓ SandboxService 创建成功")
    print(f"  超时: {sandbox_service.timeout}s")
    print("✓ DataAnalyzer 创建成功")
    print("✓ JournalState 创建成功")

    # ========== 步骤 2: 创建 DSAT 操作器 ==========
    print("\n步骤 2: 创建 DSAT 操作器")
    print("-"*80)

    operators = {
        "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
        "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
        "review": ReviewOperator(llm_service=llm_service),
    }

    print("✓ GenerateCodeAndPlanOperator 创建成功")
    print("✓ ExecuteAndTestOperator 创建成功")
    print("✓ ReviewOperator 创建成功")

    # ========== 步骤 3: 配置服务字典 ==========
    print("\n步骤 3: 配置服务字典")
    print("-"*80)

    services = {
        "llm": llm_service,
        "sandbox": sandbox_service,
        "workspace": workspace,
        "data_analyzer": data_analyzer,
        "state": state,
    }

    print("✓ 服务字典配置完成")

    # ========== 步骤 4: 创建自定义 Agent ==========
    print("\n步骤 4: 创建自定义 Agent")
    print("-"*80)

    agent = IntelligentSearchAgent(
        operators=operators,
        services=services,
        agent_config={
            "max_iterations": 3,  # 少量迭代以节省成本
        }
    )

    print(f"✓ Agent 创建成功: {type(agent).__name__}")

    # ========== 步骤 5: 准备数据 ==========
    print("\n步骤 5: 准备数据")
    print("-"*80)

    data_dir = Path("/Users/liufan/Applications/Github/dslighting/data/competitions/bike-sharing-demand")
    output_path = Path("/Users/liufan/Applications/Github/test_pip_dslighting/bike_submission.csv")

    if not data_dir.exists():
        print(f"✗ 数据目录不存在: {data_dir}")
        return

    print(f"✓ 数据目录: {data_dir}")
    print(f"✓ 输出路径: {output_path}")

    # ========== 步骤 6: 链接数据到工作区 ==========
    print("\n步骤 6: 链接数据到工作区")
    print("-"*80)

    try:
        workspace.link_data_to_workspace(data_dir)
        print("✓ 数据已链接到工作区")
    except Exception as e:
        print(f"✗ 链接数据失败: {e}")
        return

    # ========== 步骤 7: 运行 Agent ==========
    print("\n步骤 7: 运行 Agent")
    print("="*80)
    print()

    try:
        await agent.solve(
            description="预测 bike sharing demand（共享单车租赁需求预测）",
            io_instructions="""
数据说明：
- train.csv 包含训练数据，最后一列是 'count'（租赁数量）
- test.csv 包含测试数据，需要预测 'count' 列

任务要求：
1. 从 train.csv 加载数据
2. 进行特征工程（提取时间特征、处理类别变量）
3. 训练机器学习模型（推荐使用随机森林或梯度提升）
4. 在 test.csv 上进行预测
5. 将预测结果保存到 submission.csv，格式为两列：datetime, count

注意事项：
- 确保预测值非负
- 使用适当的评估指标（如 RMSE）
- 可以尝试特征组合和交叉验证
            """,
            data_dir=data_dir,
            output_path=output_path
        )

        print("\n" + "="*80)
        print("✓ Agent 执行完成！")
        print("="*80)

        # 检查输出文件
        if output_path.exists():
            print(f"\n✓ 输出文件已生成: {output_path}")

            # 显示文件内容
            with open(output_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                total_lines = len(lines)
                print(f"  总行数: {total_lines}")
                print(f"\n文件预览（前10行）:")
                for i, line in enumerate(lines[:10], 1):
                    print(f"  {i}: {line}")
        else:
            print(f"\n✗ 输出文件未生成: {output_path}")

    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("自定义 DSAT Agent - Bike Sharing Demand")
    print("="*80)

    print("\n这个示例展示了如何:")
    print("  1. ✓ 直接基于 DSAT 创建自定义 Agent")
    print("  2. ✓ 使用所有 DSAT 服务（LLM, Sandbox, DataAnalyzer, JournalState）")
    print("  3. ✓ 使用所有 DSAT 操作器（Generate, Execute, Review）")
    print("  4. ✓ 实现智能搜索算法（迭代改进）")
    print("  5. ✓ 在真实数据集上运行")

    print("\n关键特点:")
    print("  - 完全控制 DSAT 框架")
    print("  - 灵活实现任何算法")
    print("  - 不需要修改源代码")
    print("  - 可以像 aide, data_interpreter 一样使用")

    print("\n文件位置:")
    print("  - Agent: my_agents/intelligent_search_agent.py")
    print("  - 运行: run_my_agent_bike.py")

    print("\n" + "="*80 + "\n")

    # 运行主函数
    asyncio.run(main())

    print("\n" + "="*80)
    print("\n💡 关键要点:")
    print("  1. ✓ 直接继承 DSATWorkflow（核心框架）")
    print("  2. ✓ 完全控制所有 DSAT 服务和操作器")
    print("  3. ✓ 可以实现任何复杂的 Agent 算法")
    print("  4. ✓ 不需要通过 DSLighting（那是简化层）")
    print("  5. ✓ 这才是正确的方式！")

    print("\n📁 完整文档:")
    print("  - CREATE_CUSTOM_AGENT_GUIDE.md")
    print("  - DSAT_COMPLETE_ARCHITECTURE.md")

    print("\n" + "="*80)
    print("完成！")
    print("="*80 + "\n")
