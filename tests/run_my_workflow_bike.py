"""
在 bike-sharing-demand 上运行自定义 Workflow

完整示例：创建自己的 workflow，像 aide 一样使用
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from pathlib import Path

# 导入自定义 workflow
import sys
sys.path.insert(0, '/Users/liufan/Applications/Github/test_pip_dslighting/my_llm_workflow')

from my_llm_workflow.workflow import MyLLMWorkflow

# 导入 DSAT 组件
from dsat.services.workspace import WorkspaceService
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.operators.llm_basic import GenerateCodeAndPlanOperator
from dsat.operators.code import ExecuteAndTestOperator

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

async def run_on_bike_sharing():
    """在 bike-sharing-demand 上运行自定义 workflow"""

    print("="*80)
    print("在 bike-sharing-demand 上运行 MyLLMWorkflow")
    print("="*80)

    # 1. 创建服务
    print("\n步骤 1: 创建服务")
    print("-"*80)

    workspace = WorkspaceService(run_name="my_llm_workflow_bike")
    llm_service = LLMService(
        model="gpt-4o",
        temperature=0.7
    )
    sandbox_service = SandboxService(
        workspace=workspace,
        timeout=300
    )

    print("✓ 服务创建成功")
    print(f"  - LLM 模型: {llm_service.model}")
    print(f"  - Sandbox 超时: {sandbox_service.timeout}s")

    # 2. 创建 operators
    print("\n步骤 2: 创建 operators")
    print("-"*80)

    operators = {
        "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
        "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
    }

    print("✓ Operators 创建成功")
    print(f"  - generate: LLM 代码生成")
    print(f"  - execute: Sandbox 代码执行")

    # 3. 创建 services
    print("\n步骤 3: 创建 services")
    print("-"*80)

    services = {
        "llm": llm_service,
        "sandbox": sandbox_service,
    }

    print("✓ Services 创建成功")

    # 4. 创建 workflow
    print("\n步骤 4: 创建 workflow")
    print("-"*80)

    agent_config = {
        "max_iterations": 2,  # 少量迭代以节省成本
        "temperature": 0.7
    }

    workflow = MyLLMWorkflow(
        operators=operators,
        services=services,
        agent_config=agent_config
    )

    print("✓ Workflow 创建成功")
    print(f"  - 类型: {type(workflow).__name__}")
    print(f"  - 最大迭代: {agent_config['max_iterations']}")

    # 5. 准备数据路径
    print("\n步骤 5: 准备数据路径")
    print("-"*80)

    data_dir = Path("/Users/liufan/Applications/Github/dslighting/data/competitions/bike-sharing-demand")
    output_path = Path("/Users/liufan/Applications/Github/test_pip_dslighting/bike_submission.csv")

    if not data_dir.exists():
        print(f"✗ 数据目录不存在: {data_dir}")
        return

    print(f"✓ 数据目录: {data_dir}")
    print(f"✓ 输出路径: {output_path}")

    # 6. 运行 workflow
    print("\n步骤 6: 运行 workflow")
    print("="*80)
    print("开始执行...\n")

    try:
        await workflow.solve(
            description="预测 bike sharing demand（共享单车租赁需求预测）",
            io_instructions="""
数据说明：
- train.csv 包含训练数据，最后一列是 'count'（租赁数量）
- test.csv 包含测试数据，需要预测 'count' 列

任务要求：
1. 从 train.csv 加载数据
2. 进行特征工程
3. 训练机器学习模型（推荐随机森林）
4. 在 test.csv 上进行预测
5. 将预测结果保存到 submission.csv，格式为两列：datetime, count
            """,
            data_dir=data_dir,
            output_path=output_path
        )

        print("\n" + "="*80)
        print("✓ Workflow 执行完成！")
        print("="*80)

        if output_path.exists():
            print(f"\n✓ 输出文件已生成: {output_path}")

            # 显示文件内容
            with open(output_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"\n文件预览（前5行）:")
                for line in lines[:5]:
                    print(f"  {line}")

    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("自定义 LLM Workflow - Bike Sharing Demand")
    print("="*80)
    print("\n这个示例展示了如何:")
    print("  1. 创建自定义 workflow（像 aide, data_interpreter 一样）")
    print("  2. 只依赖 dsat（不依赖 dslighting）")
    print("  3. 使用 LLM + Sandbox")
    print("  4. 在真实数据集上运行")
    print("\n" + "="*80 + "\n")

    asyncio.run(run_on_bike_sharing())

    print("\n" + "="*80)
    print("\n💡 关键要点:")
    print("  1. ✓ my_llm_workflow/workflow.py 只依赖 dsat")
    print("  2. ✓ 实现了 DSATWorkflow 接口")
    print("  3. ✓ 使用提供的 services（LLM, Sandbox）")
    print("  4. ✓ 可以直接使用，不需要修改源代码")
    print("  5. ✓ 像 aide 一样工作")

    print("\n📁 文件位置:")
    print("  - Workflow: /Users/liufan/Applications/Github/test_pip_dslighting/my_llm_workflow/workflow.py")
    print("  - 测试: /Users/liufan/Applications/Github/test_pip_dslighting/run_my_workflow_bike.py")

    print("\n" + "="*80)
    print("完成！")
    print("="*80 + "\n")
