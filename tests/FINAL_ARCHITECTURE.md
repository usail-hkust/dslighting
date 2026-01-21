# DSLighting 自定义 Agent/Workflow - 最终架构说明

## 🎯 问题回顾

您的问题非常关键：

> "本质这里应该都是dslighting的这里还是有问题"

您说得对！让我澄清整个架构。

## 📊 DSLighting 架构层次

```
┌─────────────────────────────────────────┐
│   DSLighting (用户层)                   │
│   - Agent                               │
│   - load_data()                         │
│   - 简化的 API                           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│   DSAT (框架层)                          │
│   - DSATConfig                          │
│   - DSATRunner                          │
│   - DSATWorkflow (接口)                 │
│   - Services (LLM, Sandbox, Workspace)  │
│   - Operators (Generate, Execute, etc)  │
└─────────────────────────────────────────┘
```

## ✅ 正确理解

### 1. DSLighting 和 DSAT 的关系

**DSLighting** = 简化的用户接口，内部使用 DSAT

**DSAT** = 实际的执行框架

### 2. 自定义 Workflow 应该依赖什么？

**答案**: 只依赖 DSAT！

```python
# ✓ 正确：只依赖 dsat
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService

# ✗ 错误：依赖 dslighting
from dslighting import Action, Context, Tool  # 这些是 DSLighting 2.0 的
```

### 3. DSLighting 2.0 Core Protocols 的位置

**DSLighting 2.0 的 Action, Context, Tool** 是另一套简化的协议：

```
dslighting/
├── agents/
│   └── base.py  ← Action, Context, BaseAgent (DSLighting 2.0)
└── tools/
    └── base.py  ← Tool, ToolRegistry (DSLighting 2.0)
```

**但是！创建自定义 workflow 时，应该使用 DSAT 的接口！**

## 🎯 正确的自定义 Workflow 实现

### 完整代码

```python
# my_workflow.py

# ✓ 只导入 dsat
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.operators.base import Operator
from pathlib import Path
from typing import Dict, Any

class MyWorkflow(DSATWorkflow):
    """
    我的自定义 Workflow

    只依赖 DSAT，完全独立
    """

    def __init__(self,
                 operators: Dict[str, Operator],
                 services: Dict[str, Any],
                 agent_config: Dict[str, Any]):
        super().__init__(operators, services, agent_config)

        # 获取服务（由 DSAT 提供）
        self.llm_service: LLMService = services["llm"]
        self.sandbox_service: SandboxService = services["sandbox"]

        # 获取操作器（由 DSAT 提供）
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]

    async def solve(self,
                   description: str,
                   io_instructions: str,
                   data_dir: Path,
                   output_path: Path) -> None:
        """
        实现 DSATWorkflow 接口

        Args:
            description: 任务描述
            io_instructions: I/O 指令
            data_dir: 数据目录
            output_path: 输出路径
        """
        # 1. 使用 LLM 生成代码
        code = await self._generate_code(description, io_instructions)

        # 2. 在 Sandbox 中执行
        result = await self.execute_op(code=code, mode="script")

        # 3. 迭代优化
        # ...
```

## 📁 放在哪里？

### 选项1: 放在 DSLighting 源码中（需要修改源码）

```
dslighting/dsat/workflows/manual/
└── my_workflow.py  # ← 添加到这里
```

然后在 `dsat/workflows/factory.py` 中注册。

### 选项2: 放在任何地方（推荐）✅

```
/Users/username/my_workflows/
└── my_workflow.py  # ← 放在这里
```

然后直接导入和使用：

```python
import sys
sys.path.insert(0, '/Users/username/my_workflows')

from my_workflow import MyWorkflow
# ... 使用
```

## 🚀 完整使用示例

### 步骤1: 创建 workflow.py

```python
# /path/to/my_workflow.py
from dsat.workflows.base import DSATWorkflow
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.operators.base import Operator
from pathlib import Path
from typing import Dict, Any

class MyWorkflow(DSATWorkflow):
    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)
        self.llm_service = services["llm"]
        self.sandbox_service = services["sandbox"]
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 生成代码
        system_prompt = f"Task: {description}\nI/O: {io_instructions}"
        _, code = await self.generate_op(system_prompt=system_prompt)

        # 执行代码
        result = await self.execute_op(code=code, mode="script")

        if result.success:
            print(f"✓ Success: {result.stdout}")
        else:
            print(f"✗ Failed: {result.stderr}")
```

### 步骤2: 使用 workflow

```python
# test_my_workflow.py
from dotenv import load_dotenv
load_dotenv()

import asyncio
from pathlib import Path

# 导入 workflow
from my_workflow import MyWorkflow

# 导入 DSAT 组件
from dsat.services.workspace import WorkspaceService
from dsat.services.llm import LLMService
from dsat.services.sandbox import SandboxService
from dsat.operators.llm_basic import GenerateCodeAndPlanOperator
from dsat.operators.code import ExecuteAndTestOperator

async def main():
    # 创建服务
    workspace = WorkspaceService(run_name="test")
    llm_service = LLMService(model="gpt-4o")
    sandbox_service = SandboxService(workspace=workspace, timeout=300)

    # 创建 operators
    operators = {
        "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
        "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
    }

    # 创建 services
    services = {
        "llm": llm_service,
        "sandbox": sandbox_service,
    }

    # 创建 workflow
    workflow = MyWorkflow(
        operators=operators,
        services=services,
        agent_config={"max_iterations": 3}
    )

    # 运行
    await workflow.solve(
        description="预测 bike sharing demand",
        io_instructions="读取 train.csv，训练模型，预测 test.csv",
        data_dir=Path("/path/to/bike-sharing-demand"),
        output_path=Path("submission.csv")
    )

# 运行
asyncio.run(main())
```

## 📊 三个层次的对比

### 层次1: DSLighting 2.0 Core Protocols

```python
from dslighting import Action, Context, Tool
```

**用途**: 简化的用户 API，用于快速原型开发

**位置**: `dslighting/agents/base.py`, `dslighting/tools/base.py`

### 层次2: DSLighting Agent

```python
from dslighting import Agent

agent = Agent(workflow="aide")
result = agent.run(data)
```

**用途**: 简化的用户接口

**位置**: `dslighting/core/agent.py`

### 层次3: DSAT Framework

```python
from dsat.workflows.base import DSATWorkflow

class MyWorkflow(DSATWorkflow):
    async def solve(self, description, io_instructions, data_dir, output_path):
        ...
```

**用途**: 框架层，用于创建自定义 workflow

**位置**: `dsat/`

## 💡 关键点

1. **DSLighting Agent** 使用 **DSAT Workflow**
2. **自定义 Workflow** 应该实现 **DSATWorkflow** 接口
3. **只依赖 dsat**，不依赖 dslighting
4. **不需要修改源代码**，可以直接使用

## ✅ 最终答案

### Q: "本质这里应该都是dslighting的"

**A**: 不对！应该是 **dsat**！

```
用户层: DSLighting.Agent
    ↓ 使用
框架层: DSAT + DSATWorkflow ← 你在这里实现
    ↓ 提供
服务层: Services (LLM, Sandbox, Operators)
```

### Q: "我需要像 aide 那些agent一样，用自己开发一个agent"

**A**: 是的！创建一个实现 `DSATWorkflow` 的类：

```python
class MyWorkflow(DSATWorkflow):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 你的逻辑
        pass
```

### Q: "然后可以在bike哪里跑任务"

**A**: 是的！使用上面的方式：

```python
workflow = MyWorkflow(operators, services, agent_config)
await workflow.solve(
    description="预测 bike demand",
    io_instructions="...",
    data_dir=Path("path/to/bike-sharing-demand"),
    output_path=Path("submission.csv")
)
```

## 🎯 总结

1. **DSLighting** = 用户接口
2. **DSAT** = 执行框架
3. **自定义 Workflow** = 实现 DSATWorkflow 接口
4. **只依赖 dsat**，不依赖 dslighting
5. **不需要修改源代码**

---

**文件**: `/Users/liufan/Applications/Github/test_pip_dslighting/my_llm_workflow/workflow.py`
**测试**: `/Users/liufan/Applications/Github/test_pip_dslighting/test_my_workflow.py`
**指南**: `/Users/liufan/Applications/Github/test_pip_dslighting/MY_WORKFLOW_GUIDE.md`
