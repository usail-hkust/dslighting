"""
我的第一个自定义 Agent - 完整可运行示例

这个示例展示如何从零开始创建一个自定义 Agent
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============================================================================
# 第一步：导入需要的组件（全部从 dslighting）
# ============================================================================

from dslighting import (
    # 核心
    BaseAgent,

    # 服务
    LLMService,
    SandboxService,
    WorkspaceService,
    JournalState,

    # 操作器
    GenerateCodeAndPlanOperator,
    ExecuteAndTestOperator,
    ReviewOperator,
)

# ============================================================================
# 第二步：定义你的 Agent
# ============================================================================

class MyFirstAgent(BaseAgent):
    """
    我的第一个 Agent

    策略：生成代码 → 执行 → 如果失败就重试一次
    """

    def __init__(self, operators, services, agent_config):
        # 调用父类初始化
        super().__init__(operators, services, agent_config)

        # 保存操作器
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

        # 保存配置
        self.max_retries = agent_config.get("max_retries", 2)

    async def solve(self, description, io_instructions, data_dir, output_path):
        """
        实现 Agent 的核心逻辑

        Args:
            description: 任务描述
            io_instructions: 输入输出说明
            data_dir: 数据目录
            output_path: 输出路径
        """

        print(f"\n{'='*70}")
        print(f"MyFirstAgent 开始工作")
        print(f"{'='*70}\n")

        # 尝试 1: 首次生成和执行
        print("📝 第1次尝试：生成代码...")
        plan, code = await self._generate_code(description, data_dir)
        result = await self._execute_code(code)

        # 如果成功，直接返回
        if result.success:
            print("✅ 首次执行成功！")
            await self._review_result(description, code, result)
            return

        # 如果失败，尝试修复
        print(f"\n❌ 首次执行失败")
        print(f"错误信息: {result.stderr[:200]}...")

        for retry in range(self.max_retries):
            print(f"\n📝 第{retry + 2}次尝试：修复代码...")

            # 生成修复后的代码
            fixed_code = await self._fix_code(code, result.stderr)

            # 执行修复后的代码
            result = await self._execute_code(fixed_code)

            if result.success:
                print("✅ 修复成功！")
                code = fixed_code
                await self._review_result(description, code, result)
                return
            else:
                print(f"❌ 修复失败: {result.stderr[:200]}...")
                code = fixed_code  # 保存当前代码用于下次修复

        print(f"\n⚠️  达到最大重试次数，任务失败")

    # ==================== 辅助方法 ====================

    async def _generate_code(self, description, data_dir):
        """生成代码"""
        prompt = f"""
You are a data scientist. Your task is: {description}

Data directory: {data_dir}

Please:
1. Load the data
2. Analyze the data
3. Create a solution
4. Save the output to submission.csv

Provide your solution in Python code.
"""

        plan, code = await self.generate_op(system_prompt=prompt)
        print(f"生成的计划: {plan[:100]}...")
        print(f"生成的代码长度: {len(code)} 字符")

        return plan, code

    async def _execute_code(self, code):
        """执行代码"""
        result = await self.execute_op(code=code, mode="script")

        if result.success:
            print(f"✅ 执行成功")
            print(f"输出预览: {result.stdout[:200]}...")
        else:
            print(f"❌ 执行失败")

        return result

    async def _fix_code(self, code, error_message):
        """修复代码"""
        fix_prompt = f"""
The following code has an error. Please fix it.

Code:
```python
{code}
```

Error:
```
{error_message}
```

Please provide the fixed code. Return only the code in a ```python``` block.
"""

        _, fixed_code = await self.generate_op(system_prompt=fix_prompt)
        return fixed_code

    async def _review_result(self, description, code, result):
        """审查结果"""
        review = await self.review_op(prompt_context={
            "task": description,
            "code": code,
            "output": result.stdout
        })

        print(f"\n{'='*70}")
        print(f"审查结果:")
        print(f"{'='*70}")
        print(f"分析: {review.summary[:200]}...")
        if review.metric_value:
            print(f"分数: {review.metric_value}")
        print(f"{'='*70}\n")


# ============================================================================
# 第三步：创建并运行 Agent
# ============================================================================

async def main():
    """主函数"""

    print("\n" + "="*70)
    print("我的第一个自定义 Agent - 演示")
    print("="*70)

    # 3.1 创建服务
    print("\n📦 创建服务...")
    workspace = WorkspaceService(run_name="my_first_agent")
    llm_service = LLMService(model="gpt-4o-mini")  # 使用更便宜的模型
    sandbox_service = SandboxService(workspace=workspace, timeout=300)
    state = JournalState()

    print("   ✓ Workspace 服务创建完成")
    print("   ✓ LLM 服务创建完成")
    print("   ✓ Sandbox 服务创建完成")
    print("   ✓ Journal 状态创建完成")

    # 3.2 创建操作器
    print("\n🔧 创建操作器...")
    operators = {
        "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
        "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
        "review": ReviewOperator(llm_service=llm_service),
    }

    print("   ✓ Generate 操作器创建完成")
    print("   ✓ Execute 操作器创建完成")
    print("   ✓ Review 操作器创建完成")

    # 3.3 创建服务字典
    services = {
        "llm": llm_service,
        "sandbox": sandbox_service,
        "workspace": workspace,
        "state": state,
    }

    # 3.4 创建 Agent
    print("\n🤖 创建 Agent...")
    agent = MyFirstAgent(
        operators=operators,
        services=services,
        agent_config={
            "max_retries": 2,  # 最多重试2次
        }
    )
    print("   ✓ Agent 创建完成")

    # 3.5 运行 Agent
    print("\n🚀 运行 Agent...")

    # 使用一个简单的测试任务
    data_dir = Path("/Users/liufan/Applications/Github/dslighting/datasets/bike-sharing-demand")

    await agent.solve(
        description="Predict bike sharing demand. Use a simple linear regression model.",
        io_instructions="count",
        data_dir=data_dir,
        output_path=Path("submission.csv")
    )

    print("\n" + "="*70)
    print("演示完成！")
    print("="*70 + "\n")


# ============================================================================
# 第四步：运行程序
# ============================================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║           我的第一个自定义 Agent - DSLighting 2.0                   ║
║                                                                      ║
║  这个示例展示如何：                                                  ║
║  1. 从 dslighting 导入所有需要的组件                                ║
║  2. 继承 BaseAgent 创建自定义 Agent                                 ║
║  3. 使用 LLM 生成代码                                                ║
║  4. 在沙箱中执行代码                                                 ║
║  5. 如果失败就自动修复                                               ║
║                                                                      ║
╚════════════════════════════════════════════════════════════════════╝
    """)

    # 运行主函数
    asyncio.run(main())
