<div align="center">

<img src="https://raw.githubusercontent.com/usail-hkust/dslighting/main/assets/dslighting.png" alt="DSLIGHTING Logo" width="180" style="border-radius: 15px;">

# DSLIGHTING: Data Science Framework

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
  <a href="#what-dslighting-is"><img src="https://img.shields.io/badge/%E2%9A%A1-Features-blue?style=for-the-badge" alt="Core Features"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/"><img src="https://img.shields.io/badge/%F0%9D%93%9A-Docs-orange?style=for-the-badge" alt="Documentation"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/guide/getting-started.html"><img src="https://img.shields.io/badge/%F0%9D%93%96-User_Guide-purple?style=for-the-badge" alt="User Guide"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge" alt="Stars"></a>
  &nbsp;&nbsp;
  <img src="https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge" alt="Profile views">
</p>

[中文](README_CN.md) · [日本語](docs/README_JA.md) · [Français](docs/README_FR.md)

</div>

<div align="center">

🎯 **Intelligent Agent Workflows** &nbsp;•&nbsp; 📊 **Interactive Data Visualization**<br>
🤖 **Automated Code Generation** &nbsp;•&nbsp; 📈 **End-to-End Task Evaluation**

[⭐ Star us](https://github.com/usail-hkust/dslighting/stargazers) &nbsp;•&nbsp; [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## New in v2.7.9 (Current)

| Feature | Description |
|---------|-------------|
| **Benchmark Mode** | Supports DABench and MLEBench benchmark families for agent evaluation |
| **DAG Mode** | Enhanced Directed Acyclic Graph (DAG) runtime for workflow orchestration |
| **Web UI** | Experimental and under active refactoring (not part of stable API surface) |

## What DSLighting Is

DSLighting is an LLM-driven data science execution framework. It supports:

- task-oriented agent execution (`run_agent`, `Agent`)
- benchmark evaluation (`DSBenchmark`)
- architecture-level customization (services/operators/workflows)

The current public API is split into two layers:

- `dslighting.api`: simplified, stable user API
- `dslighting.arch.*`: advanced architecture API for custom agent development

## Two Usage Modes

1. **Simplified API** (recommended for quick start)  
   For rapid prototyping and standard data science tasks.

2. **Architecture** (recommended for deep customization)  
   For advanced users building custom operators, workflows, and factories.

---

## Installation

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

If you hit `ModuleNotFoundError: aiofiles`, run:

```bash
pip install aiofiles
```

---

## Environment Setup

Minimal `.env`:

```bash
API_KEY=your_key
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

Optional model-specific overrides (`LLM_MODEL_CONFIGS`):

```json
{
  "openai/deepseek-ai/DeepSeek-V3.1-Terminus": {
    "api_key": ["key1", "key2"],
    "api_base": "https://api.siliconflow.cn/v1",
    "temperature": 1.0
  }
}
```

## `config.yaml` (Optional)

`config.yaml` is optional for normal `run_agent` / `Agent` usage.

- You can run most tasks without it.
- It is mainly used by benchmark/runtime configuration and custom model pricing metadata.
- Task registries still use per-task `data_dir/<task_id>/config.yaml` (separate from root config).

Minimal example (`config.yaml`):

```yaml
run:
  enable_trajectory_logging: false
  trajectory_filename: trajectory.jsonl

llm_pricing:
  custom_models: {}
```

## Sandbox Backends (Simplified API)

`run_agent` and `Agent` support:

- `local`
- `e2b`
- `ds_sandbox`

Use explicit dotenv loading in your script:

```python
from dotenv import load_dotenv
load_dotenv()
```

### `.env` example

```bash
SANDBOX_BACKEND=local
SANDBOX_BACKEND_TYPE=docker
SANDBOX_TIMEOUT=21600
E2B_API_KEY=
SANDBOX_WORKSPACE_BASE=/tmp/ds_sandbox_workspaces
SANDBOX_PAUSED_BASE=/tmp/ds_sandbox_paused
```

### Local sandbox

```python
result = run_agent(
    task_id="bike-sharing-demand",
    sandbox_backend="local",
)
```

### E2B sandbox

```python
result = run_agent(
    task_id="bike-sharing-demand",
    sandbox_backend="e2b",
    sandbox_api_key=None,  # read from E2B_API_KEY by default
)
```

Notes:

- install SDK: `pip install e2b`
- set `E2B_API_KEY` in `.env` (or pass `sandbox_api_key`)

### DS-Sandbox

```python
result = run_agent(
    task_id="bike-sharing-demand",
    sandbox_backend="ds_sandbox",
    sandbox_backend_type="local",  # or "docker"
)
```

Notes:

- install package: `pip install ds-sandbox`
- defaults use writable paths under `/tmp` to avoid `/opt` permission issues

---

## Quick Start (Simplified API)

### One-liner execution

```python
from dotenv import load_dotenv
load_dotenv()

from dslighting.api import run_agent

result = run_agent(
    task_id="bike-sharing-demand",
    workflow="aide",   # optional
    model="gpt-4o",    # optional
)

print(result.success, result.score, result.cost)
print(result.duration, result.output, result.error)
```

### Use `Agent` directly

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

## Architecture Mode (Custom Agent Development)

Use this when you need custom operators/workflows/factories.

What each part does:
- `Operator`: one async capability unit (for example, summarize, plan, execute).
- `Workflow.solve(...)`: core async logic of your agent.
- `WorkflowFactory.create_agent(...)`: wires services + operators into a workflow instance.
- `workflow.run(...)`: sync wrapper around `solve(...)` for non-async users.

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


# Recommended for normal scripts: sync call via workflow.run(...)
def main():
    workflow = MyWorkflowFactory(model="gpt-4o").create_agent(max_iterations=3)
    result = workflow.run(data="data/competitions/bike-sharing-demand")
    print(result)

if __name__ == "__main__":
    main()
```

For most users (no custom workflow), use `Agent.run(...)`:

```python
from dslighting.api import Agent

agent = Agent(workflow="aide", model="gpt-4o")
result = agent.run(task_id="bike-sharing-demand")
print(result)
```

Usage rule:
- Normal scripts: use `workflow.run(...)` or `agent.run(...)`.
- Already inside `async def`: use `await workflow.solve(...)` (do not call `workflow.run(...)` there).

---

## RAG Usage (DSAgent / AutoMind)

RAG is enabled through workflow namespace params and backed by `VDBService`.

### File Layout

`case_dir` should contain Python case files (`*.py`), for example:

```text
experience_replay/
  case_001.py
  case_002.py
```

### Simplified API Examples

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

### Notes

- RAG params must be namespaced (`dsagent={...}` / `automind={...}`).
- `enable_rag` is `False` by default.
- Flat keys like `enable_rag=...` or `case_dir=...` are rejected.
- If `case_dir` does not exist or has no `*.py` files, retrieval returns empty results.

---

## Result Object (Single Source of Truth)

`Agent.run()` and `run_agent()` return `AgentResult`:

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

Use `DSBenchmark` for multi-task benchmark runs.

```python
from dotenv import load_dotenv
load_dotenv()

from dslighting.api import DSBenchmark
from dslighting.core import ConfigBuilder

config = ConfigBuilder().build_config(
    workflow="aide",
    model="gpt-4o",
)

benchmark = DSBenchmark("dabench", data_dir="/path/to/dabench-data")
result = benchmark.run(config=config)

print(result.results_path)
print(result.metadata_path)
```

`DSBenchmark.run(config=...)` expects a fully resolved `DSLightingConfig`.
If you rely on `.env` values or `LLM_MODEL_CONFIGS`, build the config with `ConfigBuilder` first.
Passing a bare `DSLightingConfig()` no longer triggers benchmark-side LLM env fallback.

Supported benchmark families include DABench and MLEBench variants.

If `DSBenchmark` raises an import error (for example missing `pandas`), install the missing package first:

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

## Migration Notes (Latest Standard)

Use these imports going forward:

- simplified layer: `from dslighting.api import Agent, run_agent, DSBenchmark`
- config construction: `from dslighting.core import ConfigBuilder`
- config object types: `from dslighting.config import DSLightingConfig, WorkflowConfig`
- architecture layer: `from dslighting.arch...`

Avoid introducing new imports from removed/deprecated compatibility paths.

---

## ⭐ Star History

<div align="center">

[![Stargazers repo roster for @usail-hkust/dslighting](https://reporoster.com/stars/usail-hkust/dslighting)](https://github.com/usail-hkust/dslighting/stargazers)

[![Forkers repo roster for @usail-hkust/dslighting](https://reporoster.com/forks/usail-hkust/dslighting)](https://github.com/usail-hkust/dslighting/network/members)

[![Star History Chart](https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=Date)](https://star-history.com/#usail-hkust/dslighting&Date)

</div>

---

## License

AGPL-3.0. See `LICENSE`.

## Contributing

Issues and PRs are welcome: https://github.com/usail-hkust/dslighting

## Support

- GitHub Issues: https://github.com/usail-hkust/dslighting/issues
- GitHub Discussions: https://github.com/usail-hkust/dslighting/discussions
