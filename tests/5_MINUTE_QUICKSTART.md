# DSLighting 2.0 - 5分钟快速入门

## 🎯 核心理念

**DSLighting = 数据科学 Agent 框架**

```
用户问题 → DSLighting Agent → 代码执行 → 结果
```

---

## 📊 三种使用方式

### 方式 1️⃣: 零代码（推荐新手）

```python
import dslighting

# 一行代码解决问题
result = dslighting.run_agent(task_id="bike-sharing-demand")

print(f"Score: {result.score}")
```

✅ 适合：不想写代码，直接使用

---

### 方式 2️⃣: 使用内置 Agent

```python
import dslighting

# 选择一个内置 Agent
agent = dslighting.Agent(workflow="aide")  # 或 autokaggle, data_interpreter, etc.

# 运行
result = agent.run(data="path/to/data")

print(f"Success: {result.success}")
print(f"Score: {result.score}")
```

✅ 适合：想自定义模型、参数等

---

### 方式 3️⃣: 创建自定义 Agent（核心）

```python
import asyncio
from pathlib import Path
from dslighting import (
    BaseAgent,              # ← 唯一需要记住的类
    LLMService,
    SandboxService,
    WorkspaceService,
    JournalState,
    GenerateCodeAndPlanOperator,
    ExecuteAndTestOperator,
)

# ========== 第1步: 定义你的 Agent ==========
class MyAgent(BaseAgent):
    """我的智能 Agent"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # 获取资源
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        """实现你的算法"""

        # 1. 生成代码
        prompt = f"Task: {description}"
        plan, code = await self.generate_op(system_prompt=prompt)

        # 2. 执行代码
        result = await self.execute_op(code=code, mode="script")

        # 3. 返回结果
        if result.success:
            print(f"✓ 成功！")
            print(f"输出: {result.stdout[:200]}")
        else:
            print(f"✗ 失败: {result.stderr}")

        return result

# ========== 第2步: 运行你的 Agent ==========
async def main():
    # 2.1 创建服务
    workspace = WorkspaceService(run_name="my_test")
    llm_service = LLMService(model="gpt-4o")
    sandbox_service = SandboxService(workspace=workspace)
    state = JournalState()

    # 2.2 创建操作器
    operators = {
        "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
        "execute": ExecuteAndTestOperator(sandbox_service=sandbox_service),
    }

    # 2.3 创建服务字典
    services = {
        "llm": llm_service,
        "sandbox": sandbox_service,
        "workspace": workspace,
        "state": state,
    }

    # 2.4 创建 Agent
    agent = MyAgent(operators, services, {})

    # 2.5 运行
    await agent.solve(
        description="预测 bike sharing demand",
        io_instructions="count",
        data_dir=Path("data/bike-sharing-demand"),
        output_path=Path("submission.csv")
    )

# 运行
asyncio.run(main())
```

✅ 适合：想实现自己的算法

---

## 🔑 核心概念（3个）

### 1. BaseAgent - 所有 Agent 的基类

```python
from dslighting import BaseAgent

class MyAgent(BaseAgent):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 你的算法
        pass
```

### 2. Services - 提供功能的服务

```python
from dslighting import LLMService, SandboxService, JournalState

# LLM 服务 - 调用 GPT
llm_service = LLMService(model="gpt-4o")

# Sandbox 服务 - 执行代码
sandbox_service = SandboxService(workspace=workspace)

# Journal 状态 - 管理搜索树
state = JournalState()
```

### 3. Operators - 执行具体操作

```python
from dslighting import GenerateCodeAndPlanOperator, ExecuteAndTestOperator

# 生成操作器 - 用 LLM 生成代码
generate_op = GenerateCodeAndPlanOperator(llm_service=llm_service)

# 执行操作器 - 在沙箱中运行代码
execute_op = ExecuteAndTestOperator(sandbox_service=sandbox_service)
```

---

## 💡 实际例子

### 例子 1: 简单的单次执行 Agent

```python
from dslighting import BaseAgent

class SimpleAgent(BaseAgent):
    """生成一次代码，执行一次"""

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 生成代码
        plan, code = await self.generate_op(system_prompt=f"Task: {description}")

        # 执行代码
        result = await self.execute_op(code=code, mode="script")

        return result
```

### 例子 2: 迭代优化 Agent

```python
from dslighting import BaseAgent, JournalState, Node, MetricValue

class IterativeAgent(BaseAgent):
    """多次尝试，选择最好的"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)
        self.state: JournalState = services["state"]
        self.max_iterations = agent_config.get("max_iterations", 5)

    async def solve(self, description, io_instructions, data_dir, output_path):
        best_score = float('-inf')

        for i in range(self.max_iterations):
            # 生成代码
            prompt = f"Task: {description}\nIteration: {i+1}"
            plan, code = await self.generate_op(system_prompt=prompt)

            # 执行代码
            result = await self.execute_op(code=code, mode="script")

            # 评估
            if result.success:
                score = float(result.stdout.split("Score:")[-1].strip())
                if score > best_score:
                    best_score = score
                    print(f"✓ New best: {score}")

        print(f"Final score: {best_score}")
```

### 例子 3: 使用自定义 Operator

```python
from dslighting import BaseAgent, Operator, LLMService

class SummarizeOperator(Operator):
    """自定义: 总结文本"""

    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service=llm_service, name="summarize")

    async def __call__(self, text: str) -> str:
        prompt = f"Summarize: {text}"
        return await self.llm_service.call(prompt)


class AgentWithCustomOperator(BaseAgent):
    """使用自定义操作器的 Agent"""

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        # 使用自定义操作器
        self.summarize_op = operators["summarize"]
        self.generate_op = operators["generate"]
        self.execute_op = operators["execute"]

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 先总结任务
        summary = await self.summarize_op(description)

        # 基于总结生成代码
        prompt = f"Task: {description}\nSummary: {summary}"
        plan, code = await self.generate_op(system_prompt=prompt)

        # 执行代码
        result = await self.execute_op(code=code, mode="script")

        return result
```

---

## 📦 可用的导入（全部从 dslighting）

```python
from dslighting import (
    # 核心
    BaseAgent,

    # 服务
    LLMService,
    SandboxService,
    WorkspaceService,
    DataAnalyzer,
    VDBService,

    # 状态
    JournalState,
    Node,
    MetricValue,
    Experience,

    # 操作器
    Operator,                              # 自定义操作器的基类
    GenerateCodeAndPlanOperator,
    ExecuteAndTestOperator,
    ReviewOperator,
    PlanOperator,
    SummarizeOperator,
)
```

---

## 🚀 快速开始流程

### 1. 安装

```bash
pip install dslighting
```

### 2. 设置 API Key

```bash
# .env 文件
OPENAI_API_KEY=your_key_here
```

### 3. 选择使用方式

**方式 A: 零代码**
```python
import dslighting
result = dslighting.run_agent(task_id="bike-sharing-demand")
```

**方式 B: 自定义 Agent**
```python
from dslighting import BaseAgent

class MyAgent(BaseAgent):
    async def solve(...):
        # 你的算法
        pass
```

---

## 🎯 关键要点

### ✅ 记住这3件事：

1. **BaseAgent** - 所有 Agent 的基类
2. **Services** - 提供功能（LLM、沙箱、状态）
3. **Operators** - 执行操作（生成、执行、审查）

### ✅ 三步流程：

1. **创建服务**
2. **创建操作器**
3. **创建并运行 Agent**

### ✅ 所有导入都从 `dslighting`：

```python
from dslighting import BaseAgent, LLMService, ...
```

不需要 `import dsat`！

---

## 🔗 更多资源

- **完整架构**: 见 `CLEAR_ARCHITECTURE_GUIDE.md`
- **自定义 Operators/Prompts**: 见 `HOW_TO_ADD_OPERATORS_AND_PROMPTS.md`
- **完整示例**: 见 `example_custom_operators_and_prompts.py`

---

## 💬 常见问题（30秒回答）

**Q: 我需要学习 DSAT 吗？**
A: 不需要！所有功能都从 `dslighting` 导入。

**Q: 如何开始？**
A: 运行 `dslighting.run_agent(task_id="bike-sharing-demand")` 试试！

**Q: 如何创建自己的 Agent？**
A: 继承 `BaseAgent`，实现 `solve()` 方法。

**Q: 可以自定义吗？**
A: 完全可以！自定义 Operator、Prompt、Agent 都可以。

---

## 🎉 开始吧！

```python
# 1. 零代码
import dslighting
result = dslighting.run_agent(task_id="bike-sharing-demand")

# 2. 自定义
from dslighting import BaseAgent

class MyAgent(BaseAgent):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 你的算法
        pass
```

就这么简单！🚀
