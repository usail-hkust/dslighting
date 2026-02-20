<div align="center">

<img src="https://raw.githubusercontent.com/usail-hkust/dslighting/main/assets/dslighting.png" alt="DSLIGHTING Logo" width="180" style="border-radius: 15px;">

# DSLIGHTING: 数据科学框架

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-2.7.9-blue?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/dslighting/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dslighting?style=flat-square&logo=pypi)](https://pypi.org/project/dslighting/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](LICENSE)

<p align="center">
  <a href="#quick-start-simplified-api"><img src="https://img.shields.io/badge/%F0%9F%9A%80-Quick_Start-green?style=for-the-badge" alt="Quick Start"></a>
  &nbsp;&nbsp;
  <a href="#dslighting-是什么"><img src="https://img.shields.io/badge/%E2%9A%A1-Features-blue?style=for-the-badge" alt="Core Features"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/"><img src="https://img.shields.io/badge/%F0%9D%93%9A-Docs-orange?style=for-the-badge" alt="Documentation"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/guide/getting-started.html"><img src="https://img.shields.io/badge/%F0%9D%93%96-User_Guide-purple?style=for-the-badge" alt="User Guide"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge" alt="Stars"></a>
  &nbsp;&nbsp;
  <img src="https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge" alt="Profile views">
</p>

[English](README.md) · [日本語](docs/README_JA.md) · [Français](docs/README_FR.md)

</div>

<div align="center">

🎯 **智能 Agent 工作流** &nbsp;•&nbsp; 📊 **交互式数据可视化**<br>
🤖 **自动化代码生成** &nbsp;•&nbsp; 📈 **端到端任务评测**

[⭐ Star us](https://github.com/usail-hkust/dslighting/stargazers) &nbsp;•&nbsp; [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## v2.7.9（当前版本）

| 功能 | 说明 |
|---------|-------------|
| **Benchmark Mode** | 支持 DABench 与 MLEBench 两类评测集 |
| **DAG Mode** | 增强的有向无环图（DAG）编排运行时 |
| **Web UI** | 处于重构中，暂不属于稳定 API 面 |

## DSLighting 是什么

DSLighting 是一个 LLM 驱动的数据科学执行框架，支持：

- 面向任务的 Agent 执行（`run_agent`、`Agent`）
- 基准评测（`DSBenchmark`）
- 架构级扩展（services/operators/workflows）

当前公开 API 分为两层：

- `dslighting.api`：简化、稳定、面向使用者
- `dslighting.arch.*`：高级架构 API，面向自定义 Agent 开发

## 两种使用方式

1. **Simplified API**（推荐快速上手）  
   适合快速原型和标准数据科学任务。

2. **Architecture**（推荐深度定制）  
   适合需要自定义 operators、workflows、factories 的高级场景。

---

## 安装

```bash
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting

python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -e .
```

如果遇到 `ModuleNotFoundError: aiofiles`，执行：

```bash
pip install aiofiles
```

---

## 环境变量配置

最小 `.env`：

```bash
API_KEY=your_key
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

可选模型级覆盖（`LLM_MODEL_CONFIGS`）：

```json
{
  "openai/deepseek-ai/DeepSeek-V3.1-Terminus": {
    "api_key": ["key1", "key2"],
    "api_base": "https://api.siliconflow.cn/v1",
    "temperature": 1.0
  }
}
```

## `config.yaml`（可选）

`run_agent` / `Agent` 的常规使用不依赖根目录 `config.yaml`。

- 大多数任务无需该文件即可运行。
- 该文件主要用于 benchmark/runtime 配置，以及自定义模型价格元数据。
- 任务注册仍使用每个任务目录下的 `data_dir/<task_id>/config.yaml`（与根目录配置不同）。

最小示例（`config.yaml`）：

```yaml
run:
  enable_trajectory_logging: false
  trajectory_filename: trajectory.jsonl

llm_pricing:
  custom_models: {}
```

---

## Quick Start (Simplified API)

### 一行调用

```python
from dotenv import load_dotenv
load_dotenv()

from dslighting.api import run_agent

result = run_agent(
    task_id="bike-sharing-demand",
    workflow="aide",   # 可选
    model="gpt-4o",    # 可选
)

print(result.success, result.score, result.cost)
print(result.duration, result.output, result.error)
```

### 直接使用 `Agent`

```python
from dotenv import load_dotenv
load_dotenv()

from dslighting.api import Agent

agent = Agent(
    workflow="aide",
    model="gpt-4o",
    max_iterations=5,
)

result = agent.run(task_id="bike-sharing-demand")
print(result)
```

---

## Architecture Mode（自定义 Agent 开发）

当你需要自定义 operators/workflows/factories 时使用：

```python
import asyncio

from dslighting.arch.interfaces import WorkflowFactoryInterface
from dslighting.arch.operators import Operator
from dslighting.arch.services import LLMService, SandboxService, WorkspaceService
from dslighting.arch.state import JournalState
from dslighting.arch.workflows import BaseWorkflow, BaseWorkflowFactory
from dslighting.config import LLMConfig


class SummarizeOperator(Operator):
    async def __call__(self, text: str) -> dict:
        return {"summary": text[:200]}


class MyWorkflow(BaseWorkflow):
    def __init__(self, operators, services, config=None):
        self.operators = operators
        self.services = services
        self.config = config or {}

    async def solve(self, description, io_instructions, data_dir, output_path):
        return await self.operators["summarize"](text=description)


class MyWorkflowFactory(BaseWorkflowFactory, WorkflowFactoryInterface):
    def create_agent(self, **kwargs):
        workspace = WorkspaceService(run_name="custom_arch_run")
        operators = {"summarize": SummarizeOperator()}
        services = {
            "llm": LLMService(config=LLMConfig(model=self.model)),
            "sandbox": SandboxService(workspace=workspace),
            "workspace": workspace,
            "state": JournalState(),
        }
        return MyWorkflow(operators=operators, services=services, config=kwargs)


async def main():
    workflow = MyWorkflowFactory(model="gpt-4o").create_agent(max_iterations=3)
    result = await workflow.solve(
        description="Build a model to predict bike sharing demand",
        io_instructions="Use train.csv and output submission.csv",
        data_dir="data/competitions/bike-sharing-demand",
        output_path="submission.csv",
    )
    print(result)


asyncio.run(main())
```

---

## RAG 用法（DSAgent / AutoMind）

RAG 通过 workflow 命名空间参数启用，底层由 `VDBService` 支持。

### 文件结构

`case_dir` 应包含 Python 经验案例文件（`*.py`），例如：

```text
experience_replay/
  case_001.py
  case_002.py
```

### Simplified API 示例

```python
from dslighting.api import run_agent

result = run_agent(
    task_id="bike-sharing-demand",
    workflow="dsagent",
    dsagent={"enable_rag": True, "case_dir": "./experience_replay"},
)
```

```python
from dslighting.api import run_agent

result = run_agent(
    task_id="bike-sharing-demand",
    workflow="automind",
    automind={"enable_rag": True, "case_dir": "./experience_replay"},
)
```

### 说明

- RAG 参数必须放在命名空间中（`dsagent={...}` / `automind={...}`）。
- `enable_rag` 默认值是 `False`。
- 扁平参数（如 `enable_rag=...`、`case_dir=...`）会被拒绝。
- 若 `case_dir` 不存在或无 `*.py` 文件，检索结果为空。

---

## 结果对象（唯一事实来源）

`Agent.run()` 与 `run_agent()` 返回 `AgentResult`：

```python
@dataclass
class AgentResult:
    success: bool
    output: Any
    cost: float = 0.0
    duration: float = 0.0
    score: float | None = None
    artifacts_path: Path | None = None
    workspace_path: Path | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

## Benchmarks

使用 `DSBenchmark` 执行多任务评测：

```python
from dotenv import load_dotenv
load_dotenv()

from dslighting.api import DSBenchmark, DSLightingConfig
from dslighting.config import WorkflowConfig

config = DSLightingConfig(
    workflow=WorkflowConfig(name="aide", params={})
)

benchmark = DSBenchmark("dabench", data_dir="/path/to/dabench-data")
result = benchmark.run(config=config)

print(result.results_path)
print(result.metadata_path)
```

支持 DABench 与 MLEBench 变体。

如果 `DSBenchmark` 导入时报错（例如缺少 `pandas`），先安装缺失依赖：

```bash
pip install pandas
```

---

## 🏗️ Core Architecture

```text
┌─────────────────────────────────────────┐
│ 1) Agent Orchestration Layer            │
│    Workflow lifecycle and scheduling     │
│    dslighting/workflows, runner.py       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 2) Cognitive / Operator Layer           │
│    Plan/Generate/Execute/Review          │
│    dslighting/ops, prompts, state        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 3) Execution / Service Layer            │
│    LLMService, Sandbox, Workspace, DAG   │
│    dslighting/services, runtime          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 4) Domain Core Layer                    │
│    Config, tasks, interfaces, results    │
│    dslighting/core, benchmark, datasets  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 5) Infra / Foundation Layer             │
│    error, monitoring, checkpoint, utils  │
│    dslighting/error, monitoring, utils   │
└─────────────────────────────────────────┘
```

---

## 迁移说明（最新规范）

后续请使用以下导入：

- simplified layer：`from dslighting.api import Agent, run_agent, DSBenchmark, DSLightingConfig`
- architecture layer：`from dslighting.arch...`

避免从已移除/废弃兼容路径引入新依赖。

---

## ⭐ Star History

<div align="center">

[![Stargazers repo roster for @usail-hkust/dslighting](https://reporoster.com/stars/usail-hkust/dslighting)](https://github.com/usail-hkust/dslighting/stargazers)

[![Forkers repo roster for @usail-hkust/dslighting](https://reporoster.com/forks/usail-hkust/dslighting)](https://github.com/usail-hkust/dslighting/network/members)

[![Star History Chart](https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=Date)](https://star-history.com/#usail-hkust/dslighting&Date)

</div>

---

## License

AGPL-3.0。见 `LICENSE`。

## Contributing

欢迎提交 Issue 与 PR：https://github.com/usail-hkust/dslighting

## Support

- GitHub Issues: https://github.com/usail-hkust/dslighting/issues
- GitHub Discussions: https://github.com/usail-hkust/dslighting/discussions
