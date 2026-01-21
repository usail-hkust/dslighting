<div align="center">

# DSLighting

**全流程数据科学智能助手 - End-to-End Data Science Agent**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-2.3.5-blue?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/dslighting/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dslighting?style=flat-square&logo=pypi)](https://pypi.org/project/dslighting/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](LICENSE)

[📚 完整文档](https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html) |
[🚀 快速上手](#-快速上手) |
[💻 GitHub](https://github.com/usail-hkust/dslighting) |
[🐛 问题反馈](https://github.com/usail-hkust/dslighting/issues)

</div>

---

## ✨ 特性

- 🤖 **智能 Agent 工作流**：自动化数据科学任务执行
- 🔍 **Discovery API**：探索和学习所有可用的 prompts 和 operators
- 📊 **数据管理**：统一的数据加载和任务配置系统
- 🔧 **灵活配置**：支持多种 LLM 模型（OpenAI, GLM, DeepSeek, Qwen 等）
- 📝 **完整追踪**：自动记录任务执行过程和结果
- 🧩 **可扩展架构**：轻松添加自定义任务和工作流
- 🎯 **完整 DSAT 继承**：继承所有 DSAT workflow prompts 和 operators

---

## 🚀 快速上手

### 1. 安装

```bash
pip install dslighting python-dotenv
```

#### 🍎 macOS 用户注意事项

如果你使用 **xgboost**（Agent 可能会使用），需要额外安装 OpenMP 运行时库：

```bash
brew install libomp
```

**原因**：xgboost 需要 OpenMP 库进行多线程并行计算。如果缺少这个库，运行时会出现 `XGBoostError: Library not loaded: libomp.dylib` 错误。

**验证安装**：
```bash
# 检查 libomp 是否已安装
brew list libomp

# 如果没有安装，运行：
brew install libomp
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# .env

# 指定默认使用的模型（必须设置！）
LLM_MODEL=glm-4

# 多模型配置（JSON 格式）
LLM_MODEL_CONFIGS='{
  "glm-4": {
    "api_key": ["your-key-1", "your-key-2"],
    "api_base": "https://open.bigmodel.cn/api/paas/v4",
    "temperature": 0.7,
    "provider": "openai"
  },

  "openai/deepseek-ai/DeepSeek-V3": {
    "api_key": ["sk-siliconflow-key-1", "sk-siliconflow-key-2"],
    "api_base": "https://api.siliconflow.cn/v1",
    "temperature": 1.0
  },

  "gpt-4o": {
    "api_key": "sk-your-openai-api-key",
    "api_base": "https://api.openai.com/v1",
    "temperature": 0.7
  }
}'
```

**支持的模型提供商：**
- OpenAI (GPT-4, GPT-3.5)
- 智谱 AI (GLM-4)
- SiliconFlow (DeepSeek, Qwen, Kimi 等)
- 任何兼容 OpenAI API 的服务

### 3. 运行任务

**方式 1：全局配置（推荐用于多任务）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 配置一次，全局生效
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

# 创建 Agent
agent = dslighting.Agent()

# 运行任务（只需 task_id）
result = agent.run(task_id="bike-sharing-demand")

print(f"✅ 任务完成！")
print(f"结果: {result}")
```

**方式 2：直接路径（明确清晰）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

agent = dslighting.Agent()
result = agent.run(
    task_id="bike-sharing-demand",
    data_dir="/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)
```

**方式 3：内置数据集（最简单）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 无需配置，直接使用
result = dslighting.run_agent(task_id="bike-sharing-demand")
```

**方式 4：先加载数据（灵活检查）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 先加载数据并检查
data = dslighting.load_data(
    "/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)

# 检查数据
print(data.show())

# 确认无误后运行
agent = dslighting.Agent()
result = agent.run(data)
```

### 4. 查看结果

```python
print(f"Workspace: {result.workspace_path}")
print(f"Score: {result.score}")
```

---

## 🔍 Discovery API - 探索可用组件

DSLighting 2.0 提供了强大的 Discovery API，帮助你探索和了解所有可用的 prompts 和 operators。

### 快速探索

```python
import dslighting

# 一键查看所有可用组件
dslighting.explore()
```

输出示例：
```
================================================================================
DSLighting 2.0 - Component Explorer
================================================================================

🗣️  Available Prompts
--------------------------------------------------------------------------------

NATIVE (8 items):
  - PromptBuilder
  - StructuredPromptBuilder
  - create_modeling_prompt
  - create_eda_prompt
  ...

AIDE (2 items):
  - create_improve_prompt
  - create_debug_prompt

AUTOKAGGLE (7 items):
  - get_deconstructor_prompt
  - get_phase_planner_prompt
  ...

💪 Available Operators
--------------------------------------------------------------------------------

LLM (4 items):
  - GenerateCodeAndPlanOperator
  - PlanOperator
  - ReviewOperator
  - SummarizeOperator

CODE (1 items):
  - ExecuteAndTestOperator
```

### 列出指定类别的组件

```python
# 列出所有 prompts
all_prompts = dslighting.list_prompts()
for category, functions in all_prompts.items():
    print(f"{category}: {len(functions)} prompts")

# 列出特定类别的 prompts
aide_prompts = dslighting.list_prompts(category="aide")
print(f"AIDE prompts: {aide_prompts['aide']}")

# 列出所有 operators
all_ops = dslighting.list_operators()
for category, names in all_ops.items():
    print(f"{category}: {len(names)} operators")

# 列出特定类别的 operators
llm_ops = dslighting.list_operators(category="llm")
print(f"LLM operators: {llm_ops['llm']}")
```

### 获取详细信息

```python
# 获取 prompt 的详细信息
from dslighting.prompts import get_prompt_info

info = get_prompt_info("create_improve_prompt")
print(f"Name: {info['name']}")
print(f"Category: {info['category']}")
print(f"Description: {info['description']}")
print(f"Inputs:")
for input_param in info['inputs']:
    print(f"  - {input_param['name']} ({input_param['type']})")
    print(f"    {input_param['description']}")
    print(f"    Required: {input_param['required']}")
print(f"\nExample:\n{info['example']}")
```

输出示例：
```python
{
  "name": "create_improve_prompt",
  "category": "aide",
  "description": "Create improvement prompt for AIDE workflow iteration",
  "workflow": "AIDE - Iterative code generation with review",
  "inputs": [
    {
      "name": "task_context",
      "type": "Dict[str, Any]",
      "description": "Task context containing goal and I/O requirements",
      "required": True,
      "fields": {
        "goal_and_data": "str - Task goal and data overview",
        "io_instructions": "str - Critical I/O requirements"
      }
    },
    {
      "name": "memory_summary",
      "type": "str",
      "description": "Summary of past attempts from memory",
      "required": True
    }
    # ... 更多输入参数
  ],
  "outputs": "A formatted prompt string",
  "output_format": "str - Structured prompt with role, context, and instructions",
  "example": """
from dslighting.prompts.aide_prompt import create_improve_prompt

# Input
task_context = {
    "goal_and_data": "Predict bike rental demand using historical data",
    "io_instructions": "Output must be saved to 'predictions.csv' with columns: datetime, count"
}
memory_summary = "Attempt 1 used linear regression with RMSE 0.65"
previous_code = "import pandas as pd\\nmodel = LinearRegression()..."
previous_analysis = "The model achieved RMSE 0.65 but underpredicts peak hours"

# Call
prompt = create_improve_prompt(
    task_context=task_context,
    memory_summary=memory_summary,
    previous_code=previous_code,
    previous_analysis=previous_analysis
)

# Returns formatted prompt string with all context
  """
}
```

```python
# 获取 operator 的详细信息
from dslighting.operators import get_operator_info

info = get_operator_info("PlanOperator")
print(f"Name: {info['name']}")
print(f"Category: {info['category']}")
print(f"Description: {info['description']}")
print(f"Async: {info.get('async', False)}")
print(f"Required Services: {info.get('requires_services', [])}")
print(f"\nExample:\n{info['example']}")
```

### 使用场景

**场景 1: 探索可用的 workflow prompts**
```python
# 查看所有 AIDE workflow 的 prompts
from dslighting.prompts import get_prompt_info

aide_prompts = [
    "create_improve_prompt",
    "create_debug_prompt"
]

for prompt_name in aide_prompts:
    info = get_prompt_info(prompt_name)
    print(f"\n{prompt_name}:")
    print(f"  Description: {info['description']}")
    print(f"  Inputs: {[inp['name'] for inp in info['inputs']]}")
```

**场景 2: 选择合适的 operator**
```python
# 比较 LLM operators
from dslighting.operators import get_operator_info

llm_ops = ["PlanOperator", "GenerateCodeAndPlanOperator", "ReviewOperator"]

for op_name in llm_ops:
    info = get_operator_info(op_name)
    print(f"\n{op_name}:")
    print(f"  Description: {info['description']}")
    print(f"  Input: {info['inputs']}")
    print(f"  Output: {info['outputs']}")
```

**场景 3: 学习如何使用组件**
```python
# 获取完整的使用示例
info = get_prompt_info("create_improve_prompt")
print(info['example'])  # 复制粘贴即可运行

info = get_operator_info("ReviewOperator")
print(info['example'])  # 包含完整的初始化和调用代码
```

---

## 📖 核心概念

### 数据系统

DSLighting 使用统一的数据管理系统：

- **LoadedData**：核心数据容器，封装数据集和任务配置
- **TaskDetection**：自动识别任务类型（kaggle, open_ended, datasci）
- **Registry**：管理任务配置和评分规则

**查看数据结构：**

```python
data = dslighting.load_data(...)
print(data.show())
```

输出包括：
- 任务 ID 和类型
- 数据目录结构
- CSV 文件信息
- 任务描述和评估指标

### Agent 配置

```python
# 使用默认配置
agent = dslighting.Agent()

# 等价于：
agent = dslighting.Agent(
    workflow="aide",          # 工作流类型
    model="gpt-4o-mini",      # LLM 模型（从 .env 读取）
    temperature=0.7,          # 生成温度
    max_iterations=5          # 最大迭代次数
)
```

---

## 🔧 高级配置

### 自定义任务

创建自己的数据科学任务：

**目录结构：**

```
your-project/
├── data/competitions/
│   └── your-task-name/
│       └── prepared/
│           ├── public/      # train.csv, test.csv, sampleSubmission.csv
│           └── private/     # test_answer.csv
│
└── registry/
    └── your-task-name/
        ├── config.yaml      # 任务配置
        ├── description.md   # 任务描述
        └── grade.py         # 评分脚本（可选）
```

**config.yaml 示例：**

```yaml
id: your-task-name
name: Your Task Display Name
competition_type: simple
awards_medals: false
description: your-task-name/description.md

dataset:
  answers: your-task-name/prepared/private/test_answer.csv
  sample_submission: your-task-name/prepared/public/sampleSubmission.csv

grader:
  name: rmsle  # 或 accuracy, f1, mae 等
```

**运行自定义任务：**

```python
result = agent.run(
    task_id="your-task-name",
    data_dir="/path/to/data/competitions",
    registry_dir="/path/to/registry"
)
```

### 常见问题

**Q: 为什么显示 "Score: N/A"？**

A: 这是 DSLighting 的已知问题。自动评分功能当前未启用，需要手动评分：

```python
from pathlib import Path
from mlebench.grade import grade_csv
from dsat.benchmark.mle import MLEBenchmarkRegistry

registry_dir = Path(dslighting.__file__).parent / "registry"
registry = MLEBenchmarkRegistry(registry_dir=str(registry_dir))
competition = registry.get_competition("bike-sharing-demand")

submission_files = list(result.workspace_path.glob("sandbox/submission_*.csv"))
if submission_files:
    report = grade_csv(submission_files[0], competition)
    print(f"✅ 实际 Score: {report.score}")
```

**Q: `load_dotenv()` 是必须的吗？**

A: 是的！必须在导入 `dslighting` 之前调用 `load_dotenv()` 来加载 `.env` 配置。

---

## 📚 完整文档

详细文档请访问：

- **[快速上手指南](https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html)** - 完整的安装、配置和使用教程
- **[Discovery API 指南](DISCOVERY_API_GUIDE.md)** - 探索和学习所有可用的 prompts 和 operators
- **[数据系统文档](https://luckyfan-cs.github.io/dslighting-web/api/data-system.html)** - 深入了解数据管理和核心组件
- **[GitHub 项目](https://github.com/usail-hkust/dslighting)** - 源代码和问题反馈
- **[发布说明](RELEASE_NOTES_2.1.0.md)** - DSLighting 2.1.0 更新内容

## 🎉 最新版本更新

### DSLighting 2.3.5 (2025-01-20) - 🔧 **Import Error Fix**

**✅ 完整版本：包含所有四个 bug 修复**

#### Bug #4: AgentResult 导入错误（Critical）✓ 已修复
**问题**：`ImportError: cannot import name 'AgentResult' from 'dslighting.api.agent'`
**影响**：完全无法导入 dslighting 包
**根本原因**：v2.3.4 重写了 `dslighting/api/agent.py`，但忘记添加 `AgentResult` 类定义
**修复**：
- 在 `dslighting/api/agent.py` 中添加了完整的 `AgentResult` dataclass 定义
- `AgentResult` 包含所有必要的字段：success, output, score, cost, duration, workspace_path, error, metadata
- 添加了友好的 `__repr__` 方法用于显示结果摘要

**技术细节**：
```python
@dataclass
class AgentResult:
    """Result of running an Agent on a data science task."""
    success: bool
    output: any
    cost: float = 0.0
    duration: float = 0.0
    score: Optional[float] = None
    artifacts_path: Optional[Path] = None
    workspace_path: Optional[Path] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
```

**包含的所有修复**：
- ✓ Bug #1: `load_data()` 不支持数据集名称（v2.3.3 修复）
- ✓ Bug #2: 安装失败（v2.3.3 修复）
- ✓ Bug #3: Agent 初始化错误（v2.3.4 修复）
- ✓ Bug #4: AgentResult 导入错误（v2.3.5 修复）

**升级建议**：
- **强烈推荐所有用户立即升级到 v2.3.5**
- 如果你遇到 `ImportError` 或无法导入 dslighting，请立即升级
- v2.3.5 是目前最稳定的版本，修复了所有已知的关键 bug

---

### DSLighting 2.3.4 (2025-01-20) - 🔧 **Agent Initialization Fix**

**✅ 完整版本：包含所有三个 bug 修复**

#### Bug #3: Agent 初始化错误（Critical）✓ 已修复
**问题**：`Agent(workflow="aide", model="...", max_iterations=1)` 报错 `TypeError: AIDEWorkflow.__init__() got an unexpected keyword argument 'model'`
**影响**：无法通过 `dslighting.Agent()` 创建 agent 实例
**根本原因**：`Agent` 类直接实例化 workflow，传递了错误的参数。`AIDEWorkflow.__init__()` 期望 `operators`, `services`, `agent_config`，但 `Agent` 传递了 `model`
**修复**：
- 完全重构了 `dslighting/api/agent.py`，改用工厂模式（Factory Pattern）
- 现在使用 `AIDEWorkflowFactory`, `AutoKaggleWorkflowFactory` 等工厂类来正确创建 workflow
- 工厂类正确处理 `model`, `api_key`, `api_base`, `temperature` 等参数

**技术细节**：
```python
# 修复前（错误）
self._agent = AIDE(model=model, **kwargs)  # TypeError!

# 修复后（正确）
self._factory = AIDEWorkflowFactory(
    model=model,
    api_key=api_key,
    api_base=api_base,
    provider=provider,
    temperature=temperature,
    timeout=timeout,
    keep_workspace=keep_workspace
)
```

**使用示例**：
```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# ✅ 现在可以正常工作
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    max_iterations=1
)
result = agent.run(task_id="bike-sharing-demand")
print(f"✅ Success: {result.success}")
```

**包含的所有修复**：
- ✓ Bug #1: `load_data()` 不支持数据集名称（v2.3.3 修复）
- ✓ Bug #2: 安装失败（v2.3.3 修复）
- ✓ Bug #3: Agent 初始化错误（v2.3.4 修复）

**升级建议**：
- **强烈推荐所有用户升级到 v2.3.4**
- 如果你遇到 `TypeError` 或 `ValueError: Data path not found`，请立即升级
- v2.3.4 是目前最稳定的版本

---

### DSLighting 2.3.3 (2025-01-20) - 🔧 **Critical Bug Fixes**

**⚠️ 重要：此版本修复了两个严重bug**

#### Bug #1: 安装失败（Critical）✓ 已修复
**问题**：v2.3.2 无法通过 pip 安装，因为 `setup.py` 尝试读取 `PIP_DOC/README_PIP.md` 时失败
**影响**：完全无法安装或升级 DSLighting
**修复**：
- 添加了 `try-except` 错误处理
- 创建了 `MANIFEST.in` 文件确保 README 文件被包含在源码包中
- 现在即使 README 文件缺失也能成功安装

#### Bug #2: load_data() 不支持数据集名称（High）✓ 已修复
**问题**：`load_data("bike-sharing-demand")` 报错 `ValueError: Data path not found`
**影响**：用户无法使用文档中描述的简化 API
**修复**：
- 移除了数据集目录检查代码的 `except` 块限制
- 改进了错误提示，列出所有可用的内置数据集
- 现在支持通过数据集名称加载数据

**使用示例**：
```python
import dslighting

# ✅ 现在这两种方式都可以正常工作：
# 方式1：使用数据集名称（推荐）
data = dslighting.load_data("bike-sharing-demand")

# 方式2：使用完整路径
data = dslighting.load_data("/path/to/bike-sharing-demand")

# 方式3：错误时显示可用数据集
data = dslighting.load_data("unknown-dataset")
# ValueError: Dataset 'unknown-dataset' not found.
#         Available built-in datasets: bike-sharing-demand
#         Or provide an explicit path to your data.
```

**升级建议**：
- 如果无法安装 v2.3.2，请直接升级到 v2.3.3
- 如果已安装 v2.3.2，建议升级到 v2.3.3 以获得完整的 bug 修复

---

### DSLighting 2.3.2 (2025-01-20) - ⚠️ **Broken Release**

**注意**：此版本无法安装，已被 v2.3.3 替代

---

### DSLighting 2.3.1

**Hotfix：自动修复 BaseWorkflowFactory 中不完整的 io_instructions**

---

### DSLighting 2.1.0

**重大更新：Discovery API 和完整 DSAT 继承**
- 新增 Discovery API 用于探索和学习所有可用的 prompts 和 operators
- 完整继承 DSAT workflow 的所有 prompts 和 operators
- 改进了数据加载和任务配置系统

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目基于 [AGPL-3.0 许可证](LICENSE) 发布。

---

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/usail-hkust/dslighting/issues)
- **文档**: [https://luckyfan-cs.github.io/dslighting-web/](https://luckyfan-cs.github.io/dslighting-web/)
- **PyPI**: [https://pypi.org/project/dslighting/](https://pypi.org/project/dslighting/)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️**

Made with ❤️ by [USAIL Lab](https://github.com/usail-hkust)

</div>
