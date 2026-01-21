# DSLighting 2.0 重新设计方案

## 🎯 设计原则

1. **完全继承 DSAT** - 所有核心能力来自 DSAT
2. **清晰的扩展层** - DSLighting 只做一件事：**标准化和简化**
3. **删除旧协议** - 删除 Action/Context/Plan 等旧设计
4. **JSON 格式 Prompts** - 使用 DSAT 的 prompt 模式
5. **用户友好** - 提供清晰的扩展点

---

## 📐 新架构设计

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: 用户层 (User Layer)                            │
│  用户直接使用 DSLighting API                             │
│                                                          │
│  dslighting.run_agent(task_id="bike-demand")            │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  Layer 2: 扩展层 (Extension Layer) - DSLighting 2.0     │
│  标准化和简化 DSAT 的使用                                 │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  2.1 标准 Prompts (Standard Prompts)           │     │
│  │  - 使用 JSON 格式定义                         │     │
│  │  - 统一的 prompt 模板                         │     │
│  │  - 易于扩展和自定义                           │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  2.2 标准 Agents (Standard Agents)             │     │
│  │  - 基于 DSATWorkflow/BaseAgent                 │     │
│  │  - 实现常见的 Agent 模式                       │     │
│  │  - 可直接使用或继承                            │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  2.3 工具注册 (Tool Registry)                  │     │
│  │  - 注册自定义 Operators                        │     │
│  │  - 注册自定义 Prompts                          │     │
│  │  - 注册自定义 Agents                           │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  Layer 3: 核心层 (Core Layer) - DSAT Framework           │
│  提供所有基础设施                                         │
│                                                          │
│  DSATWorkflow, Services, Operators, State, etc.         │
└──────────────────────────────────────────────────────────┘
```

---

## 🔧 核心组件设计

### 2.1 标准 Prompts (Standard Prompts)

**设计思路**：使用 DSAT 的 prompt 模式（字典 + 格式化）

**文件结构**：
```
dslighting/
├── prompts/
│   ├── __init__.py
│   ├── base.py              # 基础 prompt 工具
│   ├── templates/           # prompt 模板
│   │   ├── __init__.py
│   │   ├── data_science.py  # 数据科学 prompts
│   │   ├── code_gen.py      # 代码生成 prompts
│   │   └── analysis.py      # 分析 prompts
│   └── custom/              # 用户自定义 prompts
│       └── __init__.py
```

**使用方式**：
```python
from dslighting import BaseAgent
from dslighting.prompts import create_data_science_prompt

class MyAgent(BaseAgent):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 使用标准 prompt
        prompt = create_data_science_prompt(
            task_type="regression",
            description=description,
            data_info=str(data_dir)
        )

        plan, code = await self.generate_op(system_prompt=prompt)
```

---

### 2.2 标准 Agents (Standard Agents)

**设计思路**：基于 `BaseAgent` (DSATWorkflow)，提供常见模式

**文件结构**：
```
dslighting/
├── agents/
│   ├── __init__.py
│   ├── base.py              # 导出 BaseAgent = DSATWorkflow
│   ├── patterns/            # 标准 Agent 模式
│   │   ├── __init__.py
│   │   ├── simple.py        # SimpleAgent: 单次执行
│   │   ├── iterative.py     # IterativeAgent: 迭代优化
│   │   ├── multi_phase.py   # MultiPhaseAgent: 多阶段
│   │   └── collaborative.py # CollaborativeAgent: 多 Agent
│   └── registry.py          # Agent 注册系统
```

**使用方式**：
```python
from dslighting import IterativeAgent

# 直接使用标准 Agent
agent_config = {
    "max_iterations": 5,
    "early_stopping": True,
    "improvement_threshold": 0.01
}

agent = IterativeAgent(operators, services, agent_config)
await agent.solve(...)
```

**继承标准 Agent**：
```python
from dslighting import IterativeAgent, BaseAgent

class MyIterativeAgent(IterativeAgent):
    """基于标准 IterativeAgent，自定义改进策略"""

    async def _should_continue(self, iteration, best_score):
        # 自定义停止条件
        return iteration < 10 and best_score < 0.95

    async def _generate_improvement_prompt(self, description, best_node):
        # 自定义改进 prompt
        return f"Improve this solution...\n{best_node.code}"
```

---

### 2.3 工具注册 (Tool Registry)

**设计思路**：统一的注册系统

**文件结构**：
```
dslighting/
├── registry/
│   ├── __init__.py
│   ├── operators.py         # Operator 注册
│   ├── prompts.py           # Prompt 注册
│   └── agents.py            # Agent 注册
```

**使用方式**：
```python
import dslighting
from dslighting import Operator, LLMService

# 1. 定义自定义 Operator
class MyOperator(Operator):
    def __init__(self, llm_service: LLMService):
        super().__init__(llm_service=llm_service, name="my_operator")

    async def __call__(self, text: str) -> str:
        result = await self.llm_service.call(f"Process: {text}")
        return result

# 2. 注册到 DSLighting
dslighting.register_operator("my_operator", MyOperator)

# 3. 在 Agent 中使用
operators = {
    "generate": GenerateCodeAndPlanOperator(llm_service=llm_service),
    "my_operator": dslighting.get_operator("my_operator")(llm_service=llm_service),
}
```

---

## 🗑️ 删除旧设计

### 删除的文件/内容

1. **删除 DSLighting 2.0 旧协议**：
   - `dslighting/agents/base.py` 中的 `Action` 类
   - `dslighting/agents/base.py` 中的 `Context` 类
   - `dslighting/agents/base.py` 中的旧 `BaseAgent` Protocol

2. **保留**：
   - `dslighting/agents/__init__.py` 只导出来自 DSAT 的 `BaseAgent`

3. **修改 `dslighting/__init__.py`**：
   - 删除 `Action`, `Context` 的导入
   - 删除 `DSLightingBaseAgent` 的别名
   - 只保留来自 DSAT 的 `BaseAgent`

---

## 📝 标准化的 Prompt 设计

### 设计模式（基于 DSAT）

```python
# dslighting/prompts/base.py

from typing import Dict, Optional

def _dict_to_str(d: Dict, indent=0) -> str:
    """将字典格式化为可读的字符串（从 DSAT 复用）"""
    lines = []
    for k, v in d.items():
        prefix = ' ' * (indent * 2)
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(_dict_to_str(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{prefix}{k}:")
            for item in v:
                lines.append(' ' * ((indent + 1) * 2) + f"- {item}")
        else:
            lines.append(f"{prefix}{k}: {v}")
    return "\n".join(lines)


def create_prompt_template(prompt_dict: Dict) -> str:
    """
    创建 prompt 模板（标准方式）

    Args:
        prompt_dict: 字典格式的 prompt

    Returns:
        格式化后的字符串

    Example:
        >>> prompt = create_prompt_template({
        ...     "Role": "You are a data scientist",
        ...     "Task": "Predict demand",
        ...     "Requirements": ["Use sklearn", "Print metrics"]
        ... })
    """
    return _dict_to_str(prompt_dict)


# 标准的 Prompt 组件
def get_common_guidelines() -> Dict:
    """获取通用指南（从 DSAT 复用并扩展）"""
    return {
        "Response Format": (
            "Your response MUST start with a brief natural language plan (3-5 sentences), "
            "followed by a single, complete Python code block wrapped in ```python ... ```. "
            "Do not include any other text or headings."
        ),
        "Implementation Guidelines": [
            "The code must be a self-contained, single-file Python script.",
            "Print key metrics to standard output.",
            "Follow the I/O requirements precisely.",
            "Do not use interactive elements.",
        ]
    }
```

### 具体的 Prompt 模板

```python
# dslighting/prompts/templates/data_science.py

from typing import Dict, Optional
from ..base import create_prompt_template, get_common_guidelines

def create_eda_prompt(
    data_description: str,
    goal: str = "Explore and analyze the data"
) -> str:
    """
    创建 EDA（探索性数据分析）Prompt

    Args:
        data_description: 数据描述
        goal: 分析目标

    Returns:
        格式化的 prompt 字符串
    """
    prompt_dict = {
        "Role": "You are an expert Data Scientist specializing in exploratory data analysis.",
        "Task Goal": goal,
        "Data Description": data_description,
        "Instructions": {
            "Goal": "Perform comprehensive EDA and provide insights",
            "Steps": [
                "Load and inspect the data",
                "Show statistical summary",
                "Analyze distributions and correlations",
                "Identify patterns and outliers",
                "Provide actionable insights"
            ],
            **get_common_guidelines()
        }
    }

    return create_prompt_template(prompt_dict)


def create_modeling_prompt(
    task_type: str,  # "classification", "regression", etc.
    data_description: str,
    target_variable: str,
    requirements: Optional[Dict] = None
) -> str:
    """
    创建建模 Prompt

    Args:
        task_type: 任务类型
        data_description: 数据描述
        target_variable: 目标变量
        requirements: 额外要求

    Returns:
        格式化的 prompt 字符串
    """
    prompt_dict = {
        "Role": f"You are an expert Machine Learning Engineer specializing in {task_type}.",
        "Task Type": task_type,
        "Data Description": data_description,
        "Target Variable": target_variable,
        "Instructions": {
            "Goal": f"Build a {task_type} model with optimal performance",
            "Requirements": requirements or [
                "Use appropriate preprocessing",
                "Try multiple algorithms if needed",
                "Tune hyperparameters",
                "Print evaluation metrics",
                "Save predictions to submission.csv"
            ],
            **get_common_guidelines()
        }
    }

    return create_prompt_template(prompt_dict)


def create_debugging_prompt(
    code: str,
    error_message: str,
    context: Optional[str] = None
) -> str:
    """
    创建调试 Prompt

    Args:
        code: 出错的代码
        error_message: 错误信息
        context: 额外上下文

    Returns:
        格式化的 prompt 字符串
    """
    prompt_dict = {
        "Role": "You are an expert Python debugger.",
        "Task": "Fix the following code",
        "Code": code,
        "Error Message": error_message,
        "Context": context or "No additional context",
        "Instructions": {
            "Goal": "Analyze the error and provide fixed code",
            "Steps": [
                "Identify the root cause of the error",
                "Explain why the error occurred",
                "Provide the fixed code",
                "Ensure the fix is robust"
            ],
            "Response Format": "Return only the fixed code in a ```python``` block."
        }
    }

    return create_prompt_template(prompt_dict)
```

### 用户如何自定义 Prompt

```python
# 用户代码：my_prompts.py

from dslighting.prompts import create_prompt_template, get_common_guidelines

def create_my_custom_prompt(task: str, data_info: str) -> str:
    """
    创建我自己的 prompt

    使用标准的 prompt 格式，确保一致性
    """
    prompt_dict = {
        "Role": "You are my custom agent.",
        "Task": task,
        "Data": data_info,
        "Instructions": {
            "Goal": "Solve this specific problem",
            "My Custom Requirements": [
                "Use specific algorithm",
                "Follow my pattern",
                "Output in my format"
            ],
            **get_common_guidelines()  # 复用标准指南
        }
    }

    return create_prompt_template(prompt_dict)


# 在 Agent 中使用
from dslighting import BaseAgent

class MyAgent(BaseAgent):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 使用自定义 prompt
        from my_prompts import create_my_custom_prompt

        prompt = create_my_custom_prompt(
            task=description,
            data_info=str(data_dir)
        )

        plan, code = await self.generate_op(system_prompt=prompt)
```

---

## 🎯 标准 Agent 模式

### 1. SimpleAgent - 单次执行

```python
# dslighting/agents/patterns/simple.py

from dslighting import BaseAgent

class SimpleAgent(BaseAgent):
    """
    简单单次执行 Agent

    模式：生成代码 → 执行 → 返回结果
    适合：简单任务、快速原型
    """

    async def solve(self, description, io_instructions, data_dir, output_path):
        # 1. 生成 prompt
        prompt = self._create_prompt(description, data_dir)

        # 2. 生成代码
        plan, code = await self.generate_op(system_prompt=prompt)

        # 3. 执行代码
        result = await self.execute_op(code=code, mode="script")

        return result

    def _create_prompt(self, description, data_dir):
        """可覆盖的方法：自定义 prompt 生成"""
        return f"Task: {description}\nData: {data_dir}"
```

### 2. IterativeAgent - 迭代优化

```python
# dslighting/agents/patterns/iterative.py

from dslighting import BaseAgent, JournalState, Node, MetricValue

class IterativeAgent(BaseAgent):
    """
    迭代优化 Agent

    模式：多次尝试 → 选择最佳 → 返回
    适合：需要优化的任务
    """

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        self.state: JournalState = services["state"]
        self.max_iterations = agent_config.get("max_iterations", 5)

    async def solve(self, description, io_instructions, data_dir, output_path):
        best_score = float('-inf')

        for iteration in range(self.max_iterations):
            # 1. 生成 prompt（基于迭代）
            prompt = self._create_iteration_prompt(
                description, data_dir, iteration, best_score
            )

            # 2. 生成代码
            plan, code = await self.generate_op(system_prompt=prompt)

            # 3. 执行代码
            result = await self.execute_op(code=code, mode="script")

            # 4. 评估结果
            if result.success:
                score = await self._evaluate_result(description, code, result)

                # 5. 更新最佳
                if score > best_score:
                    best_score = score

                # 6. 记录到状态树
                node = Node(plan=plan, code=code)
                node.absorb_exec_result(result)
                node.metric = MetricValue(value=score, maximize=True)
                self.state.append(node, parent=None)

    def _create_iteration_prompt(self, description, data_dir, iteration, best_score):
        """可覆盖：自定义迭代 prompt"""
        if iteration == 0:
            return f"Task: {description}\nData: {data_dir}"
        else:
            return f"""
Task: {description}
Data: {data_dir}
Iteration: {iteration + 1}
Best score so far: {best_score}

Improve the solution to get a better score.
"""
```

### 3. MultiPhaseAgent - 多阶段

```python
# dslighting/agents/patterns/multi_phase.py

from dslighting import BaseAgent

class MultiPhaseAgent(BaseAgent):
    """
    多阶段 Agent

    模式：数据预处理 → 特征工程 → 建模 → 评估
    适合：复杂任务、需要明确阶段划分
    """

    def __init__(self, operators, services, agent_config):
        super().__init__(operators, services, agent_config)

        self.phases = agent_config.get("phases", [
            "preprocessing",
            "feature_engineering",
            "modeling",
            "evaluation"
        ])

    async def solve(self, description, io_instructions, data_dir, output_path):
        phase_results = {}

        for phase_name in self.phases:
            print(f"Running phase: {phase_name}")

            # 1. 生成阶段 prompt
            prompt = self._create_phase_prompt(
                phase_name, description, data_dir, phase_results
            )

            # 2. 生成代码
            plan, code = await self.generate_op(system_prompt=prompt)

            # 3. 执行代码
            result = await self.execute_op(code=code, mode="script")

            # 4. 保存结果
            phase_results[phase_name] = {
                "plan": plan,
                "code": code,
                "result": result
            }

            if not result.success:
                print(f"Phase {phase_name} failed, stopping")
                break

    def _create_phase_prompt(self, phase_name, description, data_dir, previous_results):
        """可覆盖：自定义阶段 prompt"""
        return f"""
Phase: {phase_name}
Task: {description}
Data: {data_dir}
Previous phases: {list(previous_results.keys())}

Focus on this phase only.
"""
```

---

## 📦 完整的文件结构

```
dslighting/
├── __init__.py                    # 主入口
│
├── core/                          # 核心 API（v1.x）
│   ├── agent.py
│   └── data_loader.py
│
├── prompts/                       # ⭐ 标准 Prompts
│   ├── __init__.py
│   ├── base.py                    # 基础工具
│   ├── templates/                 # Prompt 模板
│   │   ├── __init__.py
│   │   ├── data_science.py        # 数据科学
│   │   ├── code_gen.py            # 代码生成
│   │   └── debugging.py           # 调试
│   └── custom/                    # 用户自定义（可选）
│       └── __init__.py
│
├── agents/                        # ⭐ 标准 Agents
│   ├── __init__.py                # 只导出 BaseAgent (DSAT)
│   ├── patterns/                  # Agent 模式
│   │   ├── __init__.py
│   │   ├── simple.py              # SimpleAgent
│   │   ├── iterative.py           # IterativeAgent
│   │   ├── multi_phase.py         # MultiPhaseAgent
│   │   └── collaborative.py       # CollaborativeAgent
│   └── registry.py                # Agent 注册
│
├── operators/                     # ⭐ 标准 Operators
│   ├── __init__.py                # 导出 DSAT operators + 自定义
│   ├── custom/                    # 自定义 Operators
│   │   ├── __init__.py
│   │   └── examples.py            # 示例 operators
│   └── registry.py                # Operator 注册
│
├── registry/                      # ⭐ 统一注册系统
│   ├── __init__.py
│   ├── operators.py
│   ├── prompts.py
│   └── agents.py
│
└── utils/                         # 工具
    ├── __init__.py
    └── helpers.py
```

---

## 🚀 用户使用流程

### 场景 1: 使用标准 Prompt

```python
from dslighting import BaseAgent
from dslighting.prompts import create_modeling_prompt

class MyAgent(BaseAgent):
    async def solve(self, description, io_instructions, data_dir, output_path):
        # 使用标准 prompt
        prompt = create_modeling_prompt(
            task_type="regression",
            data_description=str(data_dir),
            target_variable=io_instructions
        )

        plan, code = await self.generate_op(system_prompt=prompt)
        result = await self.execute_op(code=code, mode="script")

        return result
```

### 场景 2: 继承标准 Agent

```python
from dslighting import IterativeAgent

class MyOptimizedAgent(IterativeAgent):
    """继承标准 IterativeAgent，自定义改进策略"""

    def _create_iteration_prompt(self, description, data_dir, iteration, best_score):
        # 自定义 prompt 生成
        return f"""
Custom optimization strategy:
Task: {description}
Iteration: {iteration + 1}
Best score: {best_score}

Please focus on:
1. Feature engineering
2. Model tuning
3. Ensemble methods
"""
```

### 场景 3: 自定义 Prompt（使用标准格式）

```python
from dslighting.prompts import create_prompt_template, get_common_guidelines

def create_my_prompt(task, data):
    prompt_dict = {
        "Role": "Expert Data Scientist",
        "Task": task,
        "Data": data,
        "Instructions": {
            "Goal": "Solve this task",
            "My Requirements": [
                "Use specific approach",
                "Follow my guidelines"
            ],
            **get_common_guidelines()  # 复用标准指南
        }
    }

    return create_prompt_template(prompt_dict)
```

---

## ✅ 总结

### 关键改进

1. ✅ **完全基于 DSAT** - 删除所有旧协议
2. ✅ **清晰的扩展层** - 标准化的 Prompts、Agents、Operators
3. ✅ **JSON 格式 Prompts** - 使用 DSAT 的模式
4. ✅ **用户友好** - 提供标准模式，易于继承和自定义
5. ✅ **统一注册** - 清晰的扩展机制

### 用户的三个层次

1. **使用层**：直接调用 `dslighting.run_agent()`
2. **继承层**：继承 `SimpleAgent`, `IterativeAgent` 等
3. **自定义层**：使用标准 Prompt 格式自定义

### 开始使用

```python
from dslighting import BaseAgent
from dslighting.prompts import create_modeling_prompt

class MyAgent(BaseAgent):
    async def solve(self, description, io_instructions, data_dir, output_path):
        prompt = create_modeling_prompt(
            task_type="regression",
            data_description=str(data_dir),
            target_variable=io_instructions
        )

        plan, code = await self.generate_op(system_prompt=prompt)
        result = await self.execute_op(code=code, mode="script")

        return result
```
