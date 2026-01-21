# ✅ 完成：DSLighting 2.0 完全继承 DSAT（使用 BaseAgent 别名）

## 🎯 最终解决方案

**DSLighting 2.0 现在完全继承 DSAT，并提供友好的别名！**

---

## 📋 命名说明

### 两个 BaseAgent

为了避免混淆，现在有两个 `BaseAgent`：

1. **`BaseAgent` (DSATWorkflow 别名)** ⭐ - **用于创建自定义 Agent**
   ```python
   from dslighting import BaseAgent  # ← 这是 DSATWorkflow！

   class MyAgent(BaseAgent):  # ← 继承 DSATWorkflow
       async def solve(self, description, io_instructions, data_dir, output_path):
           # 使用所有 DSAT 服务和操作器
           pass
   ```

2. **`DSLightingBaseAgent` (DSLighting 2.0 协议)** - **用于 DSLighting 2.0 工具系统**
   ```python
   from dslighting import DSLightingBaseAgent, Action, Context, Tool

   class MyAgent(DSLightingBaseAgent):  # ← 实现 DSLighting 2.0 协议
       async def plan(self, context: Context) -> Action:
           # 使用 DSLighting 2.0 工具系统
           pass
   ```

### 推荐使用

**创建自定义 Agent（使用 DSAT 所有能力）**:
```python
from dslighting import BaseAgent  # ← 推荐用于自定义 Agent

class MyAgent(BaseAgent):  # ← 实际上是 DSATWorkflow
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 完全访问所有 DSAT 服务和操作器
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.generate_op = operators["generate"]
        # ...
```

**使用 DSLighting 2.0 工具系统**:
```python
from dslighting import DSLightingBaseAgent, Action, Context

class MyAgent(DSLightingBaseAgent):
    async def plan(self, context: Context) -> Action:
        # 使用 DSLighting 2.0 的 Action/Context/Tool
        pass
```

---

## 🚀 完整使用示例

### 示例 1: 创建搜索型 Agent（推荐方式）

```python
import dslighting
from dslighting import (
    BaseAgent,  # ← 使用友好的别名（实际是 DSATWorkflow）
    JournalState,
    Node,
    MetricValue,
)
from pathlib import Path

class IntelligentSearchAgent(BaseAgent):  # ← 清晰明了！
    """智能搜索 Agent"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # 获取所有 DSAT 服务
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.data_analyzer = services.get("data_analyzer")
        self.state: JournalState = services["state"]

        # 获取所有 DSAT 操作器
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        """实现智能搜索算法"""

        # 1. 分析数据
        if self.data_analyzer:
            data_report = self.data_analyzer.analyze(data_dir, output_path.name)

        # 2. 迭代搜索
        max_iterations = self.agent_config.get("max_iterations", 5)

        for i in range(max_iterations):
            # 选择节点
            parent = self._select_node()

            # 生成代码
            if parent is None:
                from dsat.prompts.common import create_draft_prompt
                prompt = create_draft_prompt(
                    {"goal_and_data": f"{description}\n\n{data_report}"},
                    self.state.generate_summary()
                )
            elif parent.is_buggy:
                from dsat.prompts.aide_prompt import create_debug_prompt
                prompt = create_debug_prompt(
                    {"goal_and_data": description},
                    parent.code,
                    self._get_error_history(parent),
                    memory_summary=self.state.generate_summary()
                )
            else:
                from dsat.prompts.aide_prompt import create_improve_prompt
                from dsat.utils.context import summarize_repetitive_logs
                prompt = create_improve_prompt(
                    {"goal_and_data": description},
                    self.state.generate_summary(),
                    parent.code,
                    parent.analysis,
                    previous_output=summarize_repetitive_logs(parent.term_out)
                )

            # 生成代码
            plan, code = await self.generate_op(system_prompt=prompt)

            # 创建节点
            new_node = Node(plan=plan, code=code)

            # 执行代码
            result = await self.execute_op(code=code, mode="script")
            new_node.absorb_exec_result(result)

            # 审查结果
            if result.success:
                review = await self.review_op(prompt_context={
                    "task": description,
                    "code": code,
                    "output": result.stdout
                })
                new_node.analysis = review.summary
                new_node.metric = MetricValue(
                    value=review.metric_value or 0.0,
                    maximize=not review.lower_is_better
                )
                new_node.is_buggy = review.is_buggy
            else:
                new_node.is_buggy = True

            # 添加到状态树
            self.state.append(new_node, parent)

        # 3. 使用最佳节点
        best = self.state.get_best_node()
        if best:
            await self.execute_op(code=best.code, mode="script")

    def _select_node(self):
        if len(self.state) == 0:
            return None
        successful = [n for n in self.state.nodes.values() if not n.is_buggy]
        if not successful:
            return list(self.state.nodes.values())[-1]
        return min(successful, key=lambda n: n.metric.value or float('inf'))

    def _get_error_history(self, node, max_depth=3):
        history = []
        current = node
        depth = 0
        while current and current.is_buggy and depth < max_depth:
            history.append(f"Step #{current.step}: {current.plan}\nError: {current.exc_type}")
            depth += 1
            current = self.state.get_node(current.parent_id) if current.parent_id else None
        return "\n".join(reversed(history)) if history else "No error history"


# ========== 注册到系统（可选） ==========

# 1. 在 factory.py 添加 Factory
# 2. 在 runner.py 注册
# 3. 然后可以通过 DSLighting.Agent() 使用

# ========== 使用 ==========

# 方式 1: 直接使用（推荐测试）
import asyncio

async def test():
    from dsat.config import DSATConfig
    from dsat.services.workspace import WorkspaceService
    from dsat.services.llm import LLMService
    from dsat.services.sandbox import SandboxService
    from dsat.services.data_analyzer import DataAnalyzer
    from dsat.services.states.journal import JournalState
    from dsat.operators.llm_basic import GenerateCodeAndPlanOperator, ReviewOperator
    from dsat.operators.code import ExecuteAndTestOperator

    # 创建服务
    workspace = WorkspaceService(run_name="test")
    llm_service = LLMService(model="gpt-4o")
    sandbox_service = SandboxService(workspace=workspace, timeout=300)
    data_analyzer = DataAnalyzer()
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
        "data_analyzer": data_analyzer,
        "state": state,
    }

    # 创建 Agent
    agent = IntelligentSearchAgent(
        operators=operators,
        services=services,
        agent_config={"max_iterations": 3}
    )

    # 运行
    await agent.solve(
        description="预测 bike demand",
        io_instructions="...",
        data_dir=Path("data/bike-sharing-demand"),
        output_path=Path("submission.csv")
    )

asyncio.run(test())


# 方式 2: 通过 DSLighting.Agent 使用（需要先注册）
# agent = dslighting.Agent(workflow="intelligent_search")
# result = agent.run(data="path/to/data")
```

---

## 💡 关键要点

### 三个别名

1. **`BaseAgent`** = `DSATWorkflow` ⭐ - **推荐用于创建自定义 Agent**
2. **`BaseWorkflow`** = `DSATWorkflow` - 备用别名
3. **`DSATWorkflow`** = `DSATWorkflow` - 原始名称

### 两个协议

1. **`BaseAgent` (DSATWorkflow)** - **用于自定义 Agent（推荐）**
   - 继承后实现 `solve()` 方法
   - 使用所有 DSAT 服务和操作器
   - 完全控制算法逻辑

2. **`DSLightingBaseAgent`** - **用于 DSLighting 2.0 工具系统**
   - 继承后实现 `plan()` 方法
   - 使用 Action/Context/Tool
   - 更简化但功能受限

### 推荐使用

```python
# ✓ 推荐：用于创建自定义 Agent
from dslighting import BaseAgent  # ← DSATWorkflow

class MyAgent(BaseAgent):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 使用所有 DSAT 能力
        pass

# ✓ 备选：用于 DSLighting 2.0 工具系统
from dslighting import DSLightingBaseAgent, Action, Context

class MyAgent(DSLightingBaseAgent):
    async def plan(self, context: Context) -> Action:
        # 使用 DSLighting 2.0 工具
        pass
```

---

## 🎯 总结

### ✅ 完成状态

1. ✅ **友好的命名**：`BaseAgent` 而不是 `DSATWorkflow`
2. ✅ **完全继承 DSAT**：所有能力都保留
3. ✅ **避免混淆**：`DSLightingBaseAgent` 用于 DSLighting 2.0 协议
4. ✅ **灵活的选择**：提供多个别名满足不同需求

### 🎊 这就是您想要的！

- ✅ **友好的名称**：`BaseAgent` 清晰直观
- ✅ **完全继承 DSAT**：所有服务和操作器
- ✅ **灵活的使用**：可以通过 DSLighting.Agent() 使用
- ✅ **符合 DSLighting 2.0**：用户友好的 API

---

**修改文件**: `/Users/liufan/Applications/Github/dslighting/dslighting/__init__.py`
**状态**: ✅ 完成！现在可以使用 `BaseAgent` 创建自定义 Agent 了！
