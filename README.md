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

pip install -r requirements.txt
pip install -e .
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

```python
import asyncio

from dslighting.arch.interfaces import WorkflowFactoryInterface
from dslighting.arch.operators import Operator
from dslighting.arch.services import LLMService, SandboxService, WorkspaceService
from dslighting.arch.state import JournalState
from dslighting.arch.workflows import BaseWorkflow, BaseWorkflowFactory


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
        operators = {"summarize": SummarizeOperator()}
        services = {
            "llm": LLMService(model=self.model),
            "sandbox": SandboxService(),
            "workspace": WorkspaceService(),
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

Supported benchmark families include DABench and MLEBench variants.

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

- simplified layer: `from dslighting.api import Agent, run_agent, DSBenchmark, DSLightingConfig`
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
