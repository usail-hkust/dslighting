# DSLighting 2.0 - 完全继承 DSAT

## 🎯 核心理念

**DSLighting 2.0 完全继承 DSAT 的所有能力**

用户可以：
- ✅ 从 `dslighting` 导入所有 DSAT 组件
- ✅ 像使用 DSAT 一样创建自定义 Agent
- ✅ 拥有完整的灵活性和控制权
- ✅ 不需要直接 `import dsat`

---

## ✅ 已完成

### DSLighting 现在暴露所有 DSAT 组件

**文件**: `/Users/liufan/Applications/Github/dslighting/dslighting/__init__.py`

```python
# DSLighting 重新导出所有 DSAT 组件
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.services.workspace import WorkspaceService
from dsat.services.data_analyzer import DataAnalyzer
from dsat.services.vdb import VDBService
from dsat.services.states.journal import JournalState, Node, MetricValue
from dsat.services.states.experience import Experience
from dsat.operators.base import Operator
from dsat.operators.llm_basic import (
    GenerateCodeAndPlanOperator,
    PlanOperator,
    ReviewOperator,
    SummarizeOperator
)
from dsat.operators.code import ExecuteAndTestOperator
from dsat.models.formats import Plan, ReviewResult, Task
from dsat.models.task import TaskDefinition, TaskType

# 用户可以全部从 dslighting 导入！
```

---

## 🚀 使用方式

### 方式 1: 从 DSLighting 导入 DSAT 组件（推荐）

```python
# 全部从 DSLighting 导入，不需要 import dsat
import dslighting
from dslighting import (
    DSATWorkflow,
    LLMService,
    SandboxService,
    WorkspaceService,
    DataAnalyzer,
    JournalState,
    GenerateCodeAndPlanOperator,
    ReviewOperator,
    ExecuteAndTestOperator,
)

# 创建自定义 Agent
class MyAgent(DSATWorkflow):  # ← 从 dslighting 导入
    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # 使用所有 DSLighting 暴露的 DSAT 服务
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.data_analyzer = services["data_analyzer"]
        self.state = services["state"]

        # 使用所有 DSLighting 暴露的 DSAT 操作器
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 实现你的算法
        # 完全访问所有 DSAT 能力
        pass
```

### 方式 2: 注册并使用（推荐用于生产）

#### 步骤 1: 在 factory.py 添加 Factory

**文件**: `/Users/liufan/Applications/Github/dslighting/dsat/workflows/factory.py`

```python
# 在文件开头导入
from dsat.workflows.manual.my_agent import MyAgent

# 在文件末尾添加
class MyAgentWorkflowFactory(WorkflowFactory):
    def create_workflow(self, config, benchmark=None):
        # 创建所有服务
        workspace = WorkspaceService(run_name=config.run.name)
        llm_service = LLMService(config=config.llm)
        sandbox_service = SandboxService(workspace=workspace, timeout=config.sandbox.timeout)
        data_analyzer = DataAnalyzer()
        state = JournalState()

        # 创建所有操作器
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

        # 返回 workflow
        return MyAgent(operators, services, config.agent.model_dump())
```

#### 步骤 2: 在 runner.py 注册

**文件**: `/Users/liufan/Applications/Github/dslighting/dsat/runner.py`

```python
# 导入 Factory
from dsat.workflows.factory import (
    ...
    MyAgentWorkflowFactory,  # ← 添加
)

# 注册到 WORKFLOW_FACTORIES
WORKFLOW_FACTORIES: Dict[str, WorkflowFactory] = {
    ...
    "my_agent": MyAgentWorkflowFactory(),  # ← 添加
}
```

#### 步骤 3: 使用

```python
import dslighting

# 像使用内置 workflow 一样使用
agent = dslighting.Agent(
    workflow="my_agent",  # ← 使用自定义 Agent
    model="gpt-4o",
    max_iterations=5
)

result = agent.run(data="path/to/data")

print(f"Success: {result.success}")
print(f"Score: {result.score}")
```

---

## 📦 DSLighting 暴露的所有 DSAT 组件

### 核心类
- ✅ `DSATWorkflow` - 所有 workflow 的基类

### Services (服务)
- ✅ `LLMService` - LLM 调用
- ✅ `SandboxService` - 代码执行
- ✅ `WorkspaceService` - 工作区管理
- ✅ `DataAnalyzer` - 数据分析
- ✅ `VDBService` - 向量数据库

### State (状态)
- ✅ `JournalState` - 搜索树状态
- ✅ `Node` - 搜索树节点
- ✅ `MetricValue` - 可比较的指标值
- ✅ `Experience` - 元优化状态

### Operators (操作器)
- ✅ `Operator` - 操作器基类
- ✅ `GenerateCodeAndPlanOperator` - 生成代码和计划
- ✅ `PlanOperator` - 创建结构化计划
- ✅ `ReviewOperator` - 审查和评分
- ✅ `SummarizeOperator` - 生成摘要
- ✅ `ExecuteAndTestOperator` - 执行代码

### Models (模型)
- ✅ `Plan` - 计划模型
- ✅ `ReviewResult` - 审查结果
- ✅ `Task` - 任务模型
- ✅ `TaskDefinition` - 任务定义
- ✅ `TaskType` - 任务类型

---

## 🎨 完整示例

### 示例 1: 创建搜索型 Agent

```python
import dslighting
from dslighting import DSATWorkflow, JournalState, Node, MetricValue
from pathlib import Path

class MySearchAgent(DSATWorkflow):
    """搜索型 Agent（类似 AIDE）"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.data_analyzer = services.get("data_analyzer")
        self.state: JournalState = services["state"]
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]
        self.review_op = operators["review"]

    async def solve(self, description, io_instructions, data_dir, output_path):
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
                prompt = create_draft_prompt(...)
            elif parent.is_buggy:
                prompt = create_debug_prompt(...)
            else:
                prompt = create_improve_prompt(...)

            plan, code = await self.generate_op(system_prompt=prompt)

            # 执行
            result = await self.execute_op(code=code, mode="script")

            # 审查
            review = await self.review_op(...)

            # 保存到状态树
            node = Node(plan=plan, code=code)
            node.absorb_exec_result(result)
            self.state.append(node, parent)

        # 3. 使用最佳节点
        best = self.state.get_best_node()
        await self.execute_op(code=best.code, mode="script")
```

### 示例 2: 创建计划执行型 Agent

```python
import dslighting
from dslighting import DSATWorkflow, PlanOperator

class MyPlanExecuteAgent(DSATWorkflow):
    """计划执行型 Agent（类似 Data Interpreter）"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)
        self.sandbox_service = services["sandbox"]
        self.plan_op = operators["planner"]
        self.generator_op = operators["generator"]
        self.executor_op = operators["executor"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 1. 创建计划
        plan = await self.plan_op(user_request=description)

        # 2. 在 Notebook 中执行
        async with self.sandbox_service.notebook_executor() as notebook:
            for task in plan.tasks:
                # 生成代码
                _, code = await self.generator_op(
                    system_prompt=f"Task: {task.instruction}"
                )

                # 执行代码
                result = await self.executor_op(
                    code=code,
                    mode="notebook",
                    executor_context=notebook
                )

                # 如果失败，调试
                if not result.success:
                    _, fixed_code = await self.debugger_op(...)
                    result = await self.executor_op(
                        code=fixed_code,
                        mode="notebook",
                        executor_context=notebook
                    )
```

---

## 💡 关键优势

### ✅ 完全继承

- ✅ DSLighting 暴露所有 DSAT 组件
- ✅ 用户从 `dslighting` 导入，不需要 `import dsat`
- ✅ 完全访问 DSAT 的所有能力

### ✅ 灵活强大

- ✅ 可以实现任何复杂算法
- ✅ 完全控制所有服务和操作器
- ✅ 像使用 DSAT 一样使用 DSLighting

### ✅ 简单易用

- ✅ 通过 DSLighting.Agent() 使用
- ✅ 像内置 workflow 一样注册
- ✅ 两种使用方式（注册或直接使用）

---

## 🎯 总结

### 之前的问题

```python
# ❌ 用户需要直接导入 DSAT
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
# ...
```

### 现在的解决方案

```python
# ✅ 用户从 DSLighting 导入
import dslighting
from dslighting import DSATWorkflow, LLMService, ...

class MyAgent(DSATWorkflow):
    pass

# 然后通过 DSLighting 使用
agent = dslighting.Agent(workflow="my_agent")
result = agent.run(data="...")
```

### 核心要点

1. ✅ **DSLighting 完全继承 DSAT**
2. ✅ **用户从 DSLighting 导入所有组件**
3. ✅ **可以像 DSAT 一样定义 Agent**
4. ✅ **通过 DSLighting.Agent() 使用**
5. ✅ **这就是您想要的！**

---

**文件位置**:
- 修改: `/Users/liufan/Applications/Github/dslighting/dslighting/__init__.py`
- 测试: `/Users/liufan/Applications/Github/test_pip_dslighting/test_dslighting_inherits_dsat.py`

**状态**: ✅ 完成！DSLighting 现在完全继承了 DSAT 的所有能力！
