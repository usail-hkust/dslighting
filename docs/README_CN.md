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

## 2026-08 🎉

我们的 EMNLP 2026 Findings 论文 **DSFlow: Evolutionary Workflow Optimization for Generalizable LLM-Based Data Science Automation** 提出通过进化式 workflow 优化，构建可跨任务、跨 LLM backbone 泛化的数据科学 Agent。[下载 PDF](papers/dsflow-emnlp2026-findings.pdf)

<details>
<summary><strong>News 2026.03</strong> · <a href="#benchmarks">跳转到 Benchmarks</a></summary>

DSLighting 现已正式支持以下 benchmark 评测集：[DACode (EMNLP 2024)](https://github.com/yiyihum/da-code)、[DABench (ICML 2024)](https://github.com/InfiAgent/InfiAgent/tree/main)、[MoSciBench (ICLR 2026)](https://github.com/usail-hkust/MoSciBench)、[MLE-Bench](https://github.com/openai/mle-bench/)、[ScienceAgentBench (ICLR 2025)](https://github.com/OSU-NLP-Group/ScienceAgentBench)。

通过 `DSBenchmark`，只需几行代码就可以运行 benchmark 评测。

</details>

## v2.7.9（当前版本）

| 功能 | 说明 |
|---------|-------------|
| **Benchmark Mode** | 正式支持 DABench、DACode、MLEBench、MoSciBench、ScienceAgentBench / ScienceBench 等 benchmark 评测集 |
| **DAG Mode** | 增强的有向无环图（DAG）编排运行时 |
| ~~**Web UI**~~ | 当前已暂停开发，且该仓库不再支持 Web UI |

## DSLighting 是什么

DSLighting 是一个 LLM 驱动的数据科学执行框架。
DSLighting 是一个由 LLM 驱动的自治数据科学执行引擎，可以将任务描述和数据集转化为迭代式的代码生成、执行、评估与改进工作流。它支持：

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

pip install -r requirements.txt  # Core runtime dependencies
pip install -e .
# Optional: full development/research dependency set
# pip install -r requirements_local.txt
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

## Sandbox 后端（Simplified API）

`run_agent` 与 `Agent` 支持以下后端：

- `local`
- `e2b`
- `ds_sandbox`

请在脚本中显式加载 dotenv：

```python
from dotenv import load_dotenv
load_dotenv()
```

### `.env` 示例

```bash
SANDBOX_BACKEND=local
SANDBOX_BACKEND_TYPE=docker
SANDBOX_TIMEOUT=21600
E2B_API_KEY=
SANDBOX_WORKSPACE_BASE=/tmp/ds_sandbox_workspaces
SANDBOX_PAUSED_BASE=/tmp/ds_sandbox_paused
```

### Local 后端

```python
result = run_agent(
    task_id="bike-sharing-demand",
    sandbox_backend="local",
)
```

### E2B 后端

```python
result = run_agent(
    task_id="bike-sharing-demand",
    sandbox_backend="e2b",
    sandbox_api_key=None,  # 默认从 E2B_API_KEY 读取
)
```

说明：

- 需要安装 SDK：`pip install e2b`
- 需要在 `.env` 设置 `E2B_API_KEY`（或显式传 `sandbox_api_key`）

### DS-Sandbox 后端

```python
result = run_agent(
    task_id="bike-sharing-demand",
    sandbox_backend="ds_sandbox",
    sandbox_backend_type="local",  # 或 "docker"
)
```

说明：

- 需要安装：`pip install ds-sandbox`
- 默认会使用 `/tmp` 下可写目录，避免 `/opt` 权限问题

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

各部分职责：
- `Operator`：一个异步能力单元（如总结、规划、执行）。
- `Workflow.solve(...)`：你的 Agent 核心异步逻辑。
- `WorkflowFactory.create_agent(...)`：把 services 和 operators 组装成 workflow。
- `workflow.run(...)`：给同步用户的包装入口（内部会调用 `solve(...)`）。

```python
from pathlib import Path
from typing import Any

from dslighting.arch.interfaces import WorkflowFactoryInterface
from dslighting.arch.operators import Operator
from dslighting.arch.services import LLMService, SandboxService, WorkspaceService
from dslighting.arch.state import JournalState
from dslighting.arch.workflows import BaseWorkflow, BaseWorkflowFactory
from dslighting.config import LLMConfig


class SummarizeOperator(Operator):
    async def __call__(self, text: str) -> dict[str, Any]:
        return {"summary": text[:200]}


class MyWorkflow(BaseWorkflow):
    def __init__(self, operators, services, agent_config=None):
        super().__init__(
            operators=operators,
            services=services,
            agent_config=agent_config or {},
        )

    async def solve(
        self,
        description: str,
        io_instructions: str,
        data_dir: Path,
        output_path: Path,
    ) -> dict[str, Any]:
        return await self.operators["summarize"](text=description)


class MyWorkflowFactory(BaseWorkflowFactory, WorkflowFactoryInterface):
    def create_agent(self, **kwargs):
        workspace = WorkspaceService(run_name="custom_arch_run")
        services = {
            "llm": LLMService(config=LLMConfig(model=self.model)),
            "sandbox": SandboxService(workspace=workspace),
            "workspace": workspace,
            "state": JournalState(),
        }
        operators = {
            "summarize": SummarizeOperator(),
        }
        return MyWorkflow(operators=operators, services=services, agent_config=kwargs)


# 普通脚本推荐：通过 workflow.run(...) 同步调用
def main():
    workflow = MyWorkflowFactory(model="gpt-4o").create_agent(max_iterations=3)
    result = workflow.run(data="data/competitions/bike-sharing-demand")
    print(result)

if __name__ == "__main__":
    main()
```

大多数用户（不自定义 workflow）建议直接使用 `Agent.run(...)`：

```python
from dslighting.api import Agent

agent = Agent(workflow="aide", model="gpt-4o")
result = agent.run(task_id="bike-sharing-demand")
print(result)
```

使用规则：
- 普通脚本：用 `workflow.run(...)` 或 `agent.run(...)`。
- 已在 `async def` 中：用 `await workflow.solve(...)`（不要再调 `workflow.run(...)`）。

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

### DSFlow baseline

[独立版 DSFlow](https://anonymous.4open.science/r/data_science_dsflow-0E54/)
已作为两阶段 workflow 接入：先用粗粒度的 plan/code 分数筛选候选，
再对 top-k 候选进行 benchmark 精评，最后在 test 模式运行选出的 workflow。

```python
from dslighting.api import DSBenchmark
from dslighting.core import ConfigBuilder

config = ConfigBuilder().build_config(
    workflow="dsflow",
    model="gpt-4o",
    dsflow={
        "max_rounds": 4,
        "top_k_selection": 2,
        "task_sample_size": 3,
    },
)

benchmark = DSBenchmark("mlebench", data_dir="/path/to/mlebench-data")
result = benchmark.run(config=config)
```

对于需要附加 HTTP header 的 OpenAI-compatible endpoint，可以按运行配置，
无需修改 OpenAI 客户端的全局状态：

```python
config = ConfigBuilder().build_config(
    workflow="dsflow",
    model="your-model",
    api_key="your-api-key",
    api_base="https://your-endpoint.example/v1/",
    provider="openai",
    default_headers={"x-foo": "true"},
)
```

选出的 workflow 会保存为运行 workspace 下的 `best_workflow.py`。

如需跳过 meta-optimization、直接评测已有 workflow，可传入
`dsflow={"best_workflow_path": "/path/to/best_workflow.py"}`。原独立版
DSFlow 中使用旧 `dsat` import 路径的 workflow 会在加载时自动迁移。

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
