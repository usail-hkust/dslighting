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
  <a href="#quick-start"><img src="https://img.shields.io/badge/%F0%9F%9A%80-Quick_Start-green?style=for-the-badge" alt="Quick Start"></a>
  &nbsp;&nbsp;
  <a href="#core-features"><img src="https://img.shields.io/badge/%E2%9A%A1-Features-blue?style=for-the-badge" alt="Core Features"></a>
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

## 🚀 New in v2.8.0 - Major Update

| Feature | Description |
|---------|-------------|
| **Benchmark Mode** | Now supports **DABench**, **MLE-Bench**, and **ScienceAgentBench** for agent evaluation |
| **DAG Mode** | Enhanced **Directed Acyclic Graph (DAG)** runtime for workflow orchestration |
| **Web UI** | Coming Soon - under iteration/refactoring |

---

> **DSLighting is an LLM-driven autonomous data science execution engine that turns task descriptions and datasets into iterative code generation, execution, evaluation, and refinement workflows.**

DSLighting 提供了一个完整的数据科学 Agent 框架，支持从简单 API 调用到深度自定义的所有场景。

## 🎯 Two Usage Modes

DSLighting 2.0 提供两种使用方式：

### 1. **Simplified API** (推荐用于快速上手)

适合快速原型开发和标准数据科学任务，类似 scikit-learn 的简单接口。

### 2. **Architecture** (推荐用于深度定制)

适合需要精细控制的复杂场景，提供完整的架构访问权限。

---

## 📦 Installation

```bash
# Step 1: Clone repository
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting

# Step 2: Create virtual environment
python3.10 -m venv dslighting_env
source dslighting_env/bin/activate  # Windows: dslighting_env\Scripts\activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Install DSLighting package
pip install -e .

# Step 5: Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

> Note: If you see `ModuleNotFoundError: aiofiles` at runtime, run `pip install aiofiles` once in the same environment.

Minimal runnable setup:

```bash
API_KEY=your_key
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

```python
from dotenv import load_dotenv
load_dotenv()  # load project-root .env

from dslighting.api import run_agent

result = run_agent(
    task_id="bike-sharing-demand",  # built-in task id
    workflow="aide",                # optional, default aide
    model="gpt-4o",                 # optional, defaults to config
)

print(result.success, result.score, result.cost)
# Common fields: success / score / cost / duration / output / error
```

---

## 🚀 Quick Start

### Mode 1: Simplified API (3 lines of code)

```python
from dotenv import load_dotenv
load_dotenv()

from dslighting.api import run_agent

# Built-in dataset - no data preparation needed!
result = run_agent(task_id="bike-sharing-demand")

print(f"Success: {result.success}")
print(f"Score: {result.score}")
print(f"Cost: ${result.cost}")
```

### Mode 2: Architecture (Full Control)

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
        io_instructions="Use train.csv for training and output submission.csv",
        data_dir="data/competitions/bike-sharing-demand",
        output_path="submission.csv",
    )
    print(result)


asyncio.run(main())
```

---

## 🏗️ Core Architecture

```
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

## 📚 API Reference

### Simplified API

#### `run_agent()` - One-liner execution

```python
result = dslighting.run_agent(
    task_id="bike-sharing-demand",  # Built-in or custom task
    workflow="aide",                 # Optional: workflow name
    model="gpt-4o"                   # Optional: model name
)
```

#### `Agent` - Main interface

```python
agent = dslighting.Agent(
    workflow="aide",        # Workflow: aide, autokaggle, dsagent, etc.
    model="gpt-4o",         # LLM model
    temperature=0.7,        # LLM temperature
    max_iterations=5,       # Max iterations (workflow-specific)
)

result = agent.run(
    task_id="bike-sharing-demand",  # Recommended
    description="Predict target column"  # Optional description
)
```

#### `DataLoader` - Load data

```python
loader = dslighting.DataLoader()

# Auto-detect data type
data = loader.load("path/to/data")

# Load specific formats
data = loader.load_csv("data.csv")
data = loader.load_dataframe(df)
data = loader.load_competition("titanic")

# Load built-in dataset
data = loader.load_built_in("bike-sharing-demand")
```

#### `setup()` - Global configuration

```python
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

# Now tasks can run with just task_id
agent = dslighting.Agent()
result = agent.run(task_id="my-task")
```

### Architecture API

#### ✅ Recommended Namespaces

```python
from dslighting.api import Agent, DSBenchmark, DSLightingConfig
from dslighting.arch.interfaces import AgentInterface, WorkflowFactoryInterface, AgentResult
from dslighting.arch.services import LLMService, SandboxService, WorkspaceService
from dslighting.arch.operators import GenerateCodeAndPlanOperator, ExecuteAndTestOperator, Pipeline
from dslighting.arch.workflows import BaseWorkflow, BaseWorkflowFactory, AIDE, AutoKaggle
from dslighting.arch.state import JournalState
from dslighting.arch.prompts import PromptBuilder
```

#### 🧠 Simplified Layer (`dslighting.api`)

```python
from dslighting.api import Agent, DSLightingConfig

agent = Agent(workflow="aide", model="gpt-4o")
result = agent.run(task_id="bike-sharing-demand")

config = DSLightingConfig()
config.workflow = {"name": "aide", "params": {"max_iterations": 3}}
```

#### 🏗️ Architecture Layer (`dslighting.arch.*`)

```python
from dslighting.arch.operators import GenerateCodeAndPlanOperator, ExecuteAndTestOperator, Pipeline
from dslighting.arch.prompts import PromptBuilder
from dslighting.arch.services import LLMService, SandboxService, WorkspaceService
from dslighting.arch.state import JournalState
from dslighting.arch.workflows import AIDE

services = {
    "llm": LLMService(model="gpt-4o"),
    "sandbox": SandboxService(),
    "workspace": WorkspaceService(),
    "state": JournalState(),
}

operators = {
    "generate": GenerateCodeAndPlanOperator(
        llm_service=services["llm"],
        prompt_builder=PromptBuilder(),
    ),
    "execute": ExecuteAndTestOperator(sandbox_service=services["sandbox"]),
}

pipeline = Pipeline([
    ("generate", operators["generate"]),
    ("execute", operators["execute"]),
])

workflow = AIDE(operators=operators, services=services, config={"max_iterations": 3})
result = await workflow.solve(
    description="Build a model to predict customer churn",
    io_instructions="Use train.csv and output submission.csv",
    data_dir="data/churn-competition",
    output_path="submission.csv",
)
```

---

## 🎨 Examples

### Example 1: Built-in Dataset (Simplest)

```python
import dslighting

result = dslighting.run_agent(task_id="bike-sharing-demand")
print(f"Score: {result.score}")
```

### Example 2: Custom Dataset with Simplified API

```python
import dslighting

# Setup data directories
dslighting.setup(
    data_parent_dir="data/competitions",
    registry_parent_dir="dslighting/registry"
)

# Run agent
agent = dslighting.Agent(workflow="aide")
result = agent.run(task_id="my-competition")
```

### Example 3: Custom Agent with Operators

```python
from dslighting.arch.operators import GenerateCodeAndPlanOperator, ExecuteAndTestOperator
from dslighting.arch.services import LLMService, SandboxService, WorkspaceService
from dslighting.arch.state import JournalState
from dslighting.arch.workflows import AIDE

# Create services
services = {
    "llm": LLMService(model="gpt-4o"),
    "sandbox": SandboxService(),
    "workspace": WorkspaceService(),
    "state": JournalState(),
}

# Define operators
operators = {
    "generate": GenerateCodeAndPlanOperator(llm_service=services["llm"]),
    "execute": ExecuteAndTestOperator(sandbox_service=services["sandbox"]),
}

# Run
workflow = AIDE(operators=operators, services=services, config={"max_iterations": 5})
result = await workflow.solve(
    description="Build a model to predict customer churn",
    io_instructions="Use train.csv for training, submit predictions on test.csv",
    data_dir="data/churn-competition",
    output_path="submission.csv"
)
```

### Example 4: Custom Workflow Factory (v2.3.0+)

```python
from dslighting.arch.operators import GenerateCodeAndPlanOperator, ExecuteAndTestOperator
from dslighting.arch.state import JournalState
from dslighting.arch.workflows import BaseWorkflow, BaseWorkflowFactory

class MyWorkflow(BaseWorkflow):
    async def solve(self, description, io_instructions, data_dir, output_path):
        _ = await self.operators["generate"](
            description=description,
            io_instructions=io_instructions,
        )
        return await self.operators["execute"](
            data_dir=data_dir,
            output_path=output_path,
        )

class MyWorkflowFactory(BaseWorkflowFactory):
    """Custom workflow factory"""

    def create_agent(self, max_iterations=3, **kwargs):
        """Only need to implement this method!"""
        operators = {
            "generate": GenerateCodeAndPlanOperator(llm_service=self.llm_service),
            "execute": ExecuteAndTestOperator(sandbox_service=self.sandbox_service),
        }

        services = {
            "llm": self.llm_service,
            "sandbox": self.sandbox_service,
            "workspace": self.workspace_service,
            "state": JournalState(),
        }

        return MyWorkflow(operators, services, {"max_iterations": max_iterations})

# Use
factory = MyWorkflowFactory(model="gpt-4o")
await factory.run_with_task_id("bike-sharing-demand")
```

### Example 5: Exploration and Discovery

```python
import dslighting

# Show help
dslighting.help()

# List available workflows
dslighting.list_workflows()

# Explore all components
dslighting.explore()

# List available operators
ops = dslighting.list_operators()
print(f"Available operators: {ops}")

# List available prompts
prompts = dslighting.list_prompts()
print(f"Available prompts: {prompts}")
```

---

## 🎯 Workflow Selection

DSLighting supports multiple workflows:

| Workflow | Description | Best For | Default Model |
|----------|-------------|----------|---------------|
| `aide` | Adaptive Iteration & Debugging | Most data science tasks | gpt-4o |
| `autokaggle` | Competition solver | Kaggle competitions, benchmarks | gpt-4o |
| `data_interpreter` | Data analysis and exploration | Data exploration, EDA | gpt-4o-mini |
| `deepanalyze` | Analysis-focused workflow | Deep analysis tasks | gpt-4o |
| `dsagent` | Structured operator-based workflow | Tasks with logging | gpt-4o |
| `automind` | Planning + reasoning with RAG | Tasks requiring knowledge base | gpt-4o |
| `aflow` | Meta-optimization selector | Automated workflow selection | gpt-4o |

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```bash
# LLM Configuration (required)
API_KEY="sk-..."
API_BASE="https://api.openai.com/v1"
LLM_MODEL="gpt-4o-mini"

# DSLighting Configuration (optional)
DSLIGHTING_DEFAULT_WORKFLOW="aide"
DSLIGHTING_WORKSPACE_DIR="./runs/dslighting"

# Multi-model Configuration (optional)
LLM_MODEL_CONFIGS='{
  "gpt-4o": {"api_key": "sk-...", "temperature": 0.5},
  "deepseek-chat": {"api_base": "https://api.siliconflow.cn/v1"}
}'
```

### Model Pricing (Optional)

Create `config.yaml` in your project directory:

```yaml
custom_model_pricing:
  gpt-4o:
    input_cost_per_token: 2.5e-06
    output_cost_per_token: 1.0e-05
  deepseek-chat:
    input_cost_per_token: 1.0e-07
    output_cost_per_token: 1.0e-07
```

> 💡 **Note**: Model pricing is optional. If not provided, DSLighting uses LiteLLM's default pricing.

---

## 📊 Result Object

```python
@dataclass
class AgentResult:
    success: bool              # Task success status
    output: Any                # Task output
    score: Optional[float]     # Evaluation score
    cost: float                # LLM cost in USD
    duration: float            # Execution time in seconds
    artifacts_path: Path       # Path to artifacts
    workspace_path: Path       # Path to workspace
    error: Optional[str]       # Error message if failed
    metadata: Dict             # Additional metadata
```

---

## 🔧 Advanced Usage

### Use `dslighting.api.Agent` Directly

```python
from dslighting.api import Agent

agent = Agent(
    workflow="aide",
    model="gpt-4o",
    max_iterations=5,
)
```

### Custom Output Path

```python
result = agent.run(
    task_id="bike-sharing-demand",
    output="my_submission.csv",
)
```

### Task ID and Description

```python
result = agent.run(
    task_id="my-experiment-001",
    description="Build a model to predict customer churn"
)
```

### Concurrent Runs (async)

```python
import asyncio
from dslighting.api import Agent

agent = Agent(workflow="aide", model="gpt-4o")

async def main():
    results = await asyncio.gather(
        agent.async_run(task_id="bike-sharing-demand"),
        agent.async_run(task_id="my-other-task"),
    )
    for i, result in enumerate(results, start=1):
        print(f"Task {i}: score={result.score}, cost=${result.cost}")

asyncio.run(main())
```

---

## 🧩 Built-in Datasets

DSLighting includes built-in datasets (v1.8.1+):

- `bike-sharing-demand` - Bike sharing demand prediction
  - Complete dataset with train/test/split
  - Ready to use, no download needed

```python
import dslighting
result = dslighting.run_agent(task_id="bike-sharing-demand")
```

---

## 📊 Benchmarks

DSLighting supports multiple benchmarks for evaluating data science agent performance:

| Benchmark | Description | Tasks |
|-----------|-------------|-------|
| **DABench** | Data Science Agent Benchmark - Comprehensive evaluation of LLM agents on data science tasks | 300+ tasks covering EDA, feature engineering, modeling, etc. |
| **MLE-bench** | Machine Learning Engineering Benchmark - Evaluates agents on ML engineering tasks | Kaggle competitions, data preprocessing, model training |
| **ScienceAgentBench** | Science Domain Agent Benchmark - Scientific research and analysis tasks | Scientific data analysis, experiment design, hypothesis testing |

### Running Benchmarks

DSLighting uses unified `DSBenchmark` API to run all benchmarks:

```python
import os
from dslighting.api import DSBenchmark, DSLightingConfig

# Configure once (single source of truth)
config = DSLightingConfig()
config.llm.model = "gpt-4o"
config.workflow = {"name": "aide", "params": {"max_iterations": 3}}
config.scheduler.max_concurrency = 128
config.scheduler.scheduler_policy = "full_parallel"
config.run.dag_runtime.enabled = True
config.run.dag_runtime.dag_mode = "fine"

# Run DABench
benchmark = DSBenchmark(
    benchmark_type="dabench",
    data_dir="/path/to/dabench/data",
    exp_name="my_dabench_run",
).run(
    config=config,
    log_path="./logs",
    verbose=True,
)

# Run MLE-bench
benchmark = DSBenchmark(
    benchmark_type="mlebench",
    data_dir="/path/to/mle_bench/data",
    exp_name="my_mle_run",
).run(
    config=config,
    log_path="./logs",
)

# Run custom benchmark (single task example)
benchmark = DSBenchmark(
    benchmark_type="custom",
    data_dir="/path/to/data/competitions",
    vendor_comp_dir="/path/to/dslighting/benchmark/vendor/mlebench/competitions",
    competitions=["bike-sharing-demand"],
    exp_name="my_custom_run",
).run(
    config=config,
    log_path="./logs",
)
```

### Environment Variables

```bash
# Data directory (required)
DSLIGHTING_DABENCH_DATA=/path/to/dabench
DSLIGHTING_MLEBENCH_DATA=/path/to/mle_bench

# Model configuration
LLM_MODEL=gpt-4o
MAX_ITERATIONS=3

# Sandbox configuration
DSLIGHTING_SANDBOX_BACKEND=local  # local, e2b, ds_sandbox
DSLIGHTING_SANDBOX_BACKEND_TYPE=docker  # for ds_sandbox
DSLIGHTING_SANDBOX_API_KEY=xxx  # for e2b
```

### DAG Optimization Mode

DSLighting supports fine-grained DAG (Directed Acyclic Graph) optimization for parallel task execution:

| Mode | Description | Use Case |
|------|-------------|----------|
| `fine` | Fine-grained DAG mode - optimizes at node level | Maximum parallelism, complex task dependencies |
| `coarse` | Coarse-grained DAG mode - optimizes at task level | Simple task dependencies, lower overhead |

```python
from dslighting.api import DSBenchmark, DSLightingConfig

config = DSLightingConfig()
config.workflow = {"name": "aide", "params": {"max_iterations": 3}}

# Task scheduling
config.scheduler.max_concurrency = 128
config.scheduler.scheduler_policy = "full_parallel"
config.scheduler.queue_policy = "fifo"

# DAG runtime configuration
config.run.dag_runtime.enabled = True
config.run.dag_runtime.dag_mode = "fine"
config.run.dag_runtime.max_inflight_nodes = 18
config.run.dag_runtime.node_timeout_seconds = 21600.0  # 6 hours
config.run.dag_runtime.max_retries = 3

benchmark = DSBenchmark("dabench", data_dir="/path/to/dabench").run(
    config=config,
    log_path="./logs",
    verbose=True,
)
```

```python
# Migration mapping
# old: dag_enabled              -> config.run.dag_runtime.enabled
# old: dag_mode                 -> config.run.dag_runtime.dag_mode
# old: max_inflight_nodes       -> config.run.dag_runtime.max_inflight_nodes
# old: dag_node_timeout_seconds -> config.run.dag_runtime.node_timeout_seconds
# old: dag_max_retries          -> config.run.dag_runtime.max_retries
```

**DAG Benefits:**
- **Parallel Execution**: Automatically identifies independent tasks that can run in parallel
- **Dependency Resolution**: Handles task dependencies automatically
- **Resource Optimization**: Maximizes GPU/CPU utilization
- **Fault Tolerance**: Automatic retry on node failures

**Performance Comparison:**
```
Wall Clock Time:
  FINE-OPT: ~XXs (with DAG optimization)
  NO-OPT:   ~XXs (without DAG)

Speedup: 2-5x faster depending on task structure
```

---

## 📚 Documentation

- **Full Documentation**: https://luckyfan-cs.github.io/dslighting-web/
- **GitHub Repository**: https://github.com/usail-hkust/dslighting
- **Bug Reports**: https://github.com/usail-hkust/dslighting/issues

### Key Documentation Files

- `README.md` - English quick start and architecture overview
- `README_CN.md` - Chinese quick start and architecture overview
- `SETUP_GUIDE.md` - Environment and dependency setup
- `examples/` - End-to-end runnable examples

---

## 🔄 Migration from v1.x

### Old Way (v1.x)

```python
from dsat.config import DSATConfig, LLMConfig, WorkflowConfig
from dsat.runner import DSATRunner
from dsat.benchmark.mle import MLEBenchmark

config = DSATConfig(
    llm=LLMConfig(model="gpt-4o-mini", api_key=os.getenv("API_KEY")),
    workflow=WorkflowConfig(name="aide")
)
runner = DSATRunner(config)
benchmark = MLEBenchmark(...)
eval_fn = runner.get_eval_function()
await benchmark.run_evaluation(eval_fn)
```

### New Way (v2.0+)

```python
import dslighting

result = dslighting.run_agent("data/competitions/titanic")
```

**Key Benefits**:
- 10x less code
- Auto-detects task types
- No async/await needed (for simplified API)
- Sensible defaults

---

## 🎓 Training Mode (Advanced) [Coming Soon]

DSLighting 2.0+ supports training with reinforcement learning:

```python
from dslighting.arch.training import LitDSAgent, KaggleReward, DatasetConverter

# Convert competition dataset to training format
converter = DatasetConverter()
train_dataset = converter.convert_to_training_format("bike-sharing-demand")

# Create reward evaluator
reward_fn = KaggleReward(metric="rmse")

# Training setup (requires VERL and other training dependencies)
# See dslighting/training/ for details
```

---

## 🏆 License

AGPL-3.0

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

**Core Contributors**:
- [luckyfan-cs](https://github.com/luckyfan-cs) - Project lead, frontend and backend
- [canchengliu](https://github.com/canchengliu) - Workflow contributions

---

## 📞 Support

- **Documentation**: https://luckyfan-cs.github.io/dslighting-web/
- **GitHub Issues**: https://github.com/usail-hkust/dslighting/issues
- **Discussions**: https://github.com/usail-hkust/dslighting/discussions

---

**DSLIGHTING - Making Data Science Automation Easy** 🚀
