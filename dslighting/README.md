# DSLighting Simplified API

A simplified, scikit-learn-style API for the DSLighting data science automation framework.

## Features

- **Simple Interface**: Run data science tasks with just a few lines of code
- **Auto-Detection**: Automatically detects task types and recommends workflows
- **Sensible Defaults**: Works out-of-the-box with environment variables
- **Full Control**: Access underlying DSAT components when needed
- **Backward Compatible**: Existing DSAT code continues to work unchanged

## Installation

```bash
# Step 1: Install DSLighting dependencies first
cd /path/to/dslighting
pip install -r requirements_local.txt

# Step 2: Install DSLighting package with simplified API
pip install -e .

# Or for development
pip install -e ".[dev]"
```

**Important**: Install the dependencies from `requirements_local.txt` first to avoid version conflicts.

## Quick Start

### Simple Usage (3 lines of code)

```python
import dslighting

data = dslighting.load_data("path/to/data")
agent = dslighting.Agent()
result = agent.run(data)

print(f"Score: {result.score}, Cost: ${result.cost}")
```

### One-Liner

```python
import dslighting

result = dslighting.run_agent("path/to/data")
```

## API Reference

### Agent Class

Main interface for running data science tasks.

```python
agent = dslighting.Agent(
    workflow="aide",           # Workflow name
    model="gpt-4o-mini",       # LLM model
    temperature=0.7,           # LLM temperature
    max_iterations=5,          # Maximum iterations
    verbose=True               # Enable logging
)

result = agent.run(data)
```

**Parameters:**
- `workflow`: Workflow name (aide, autokaggle, automind, dsagent, data_interpreter, deepanalyze, aflow)
- `model`: LLM model name (defaults to LLM_MODEL env var)
- `api_key`: API key (defaults to API_KEY env var)
- `api_base`: API base URL (defaults to API_BASE env var)
- `temperature`: LLM temperature (0.0-1.0)
- `max_iterations`: Maximum agent iterations
- `verbose`: Enable verbose logging

**Methods:**
- `run(data, **kwargs)`: Run agent on a single task
- `run_batch(data_list, **kwargs)`: Run on multiple tasks
- `get_config()`: Get underlying DSATConfig
- `get_runner()`: Get underlying DSATRunner

### AgentResult

Result object returned by `agent.run()`.

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

### DataLoader

Load data from various sources with auto-detection.

```python
loader = dslighting.DataLoader()

# Load from directory
data = loader.load("path/to/data")

# Load from CSV
data = loader.load_csv("data.csv")

# Load from DataFrame
data = loader.load_dataframe(df)

# Load competition
data = loader.load_competition("titanic", data_dir="data/competitions")
```

## Examples

### Example 1: Kaggle Competition

```python
import dslighting

# Auto-detects competition structure
result = dslighting.run_agent("data/competitions/titanic")

print(f"Score: {result.score}")
print(f"Predictions: {result.output}")
```

### Example 2: Custom Workflow

```python
import dslighting

agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.3,
    max_iterations=10
)

result = agent.run("data/competitions/house-prices")
```

### Example 3: Question Answering

```python
import dslighting

result = dslighting.run_agent("What is the result of 9*8-2?")
print(f"Answer: {result.output}")
```

### Example 4: DataFrame Input

```python
import dslighting
import pandas as pd

df = pd.read_csv("my_data.csv")

agent = dslighting.Agent()
result = agent.run(df, description="Predict the target column")
```

### Example 5: Batch Processing

```python
import dslighting

agent = dslighting.Agent()

results = agent.run_batch([
    "data/competitions/titanic",
    "data/competitions/house-prices",
    "data/competitions/fraud"
])

for i, result in enumerate(results):
    print(f"Task {i+1}: score={result.score}, cost=${result.cost}")
```

## Configuration

### Environment Variables

DSLighting reads these environment variables:

```bash
# LLM Configuration
export API_KEY="sk-..."
export API_BASE="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"
export LLM_PROVIDER="openai"

# DSLighting Configuration
export DSLIGHTING_DEFAULT_WORKFLOW="aide"
export DSLIGHTING_WORKSPACE_DIR="./runs/dslighting"

# Model-specific overrides (JSON)
export LLM_MODEL_CONFIGS='{
  "gpt-4o": {"api_key": "sk-...", "temperature": 0.5},
  "deepseek-chat": {"api_base": "https://api.siliconflow.cn/v1"}
}'
```

## Workflow Selection

DSLighting automatically recommends workflows based on task type:

| Task Type | Recommended Workflows |
|-----------|----------------------|
| Kaggle Competition (Tabular) | `autokaggle`, `aide` |
| Kaggle Competition (Time Series) | `aide`, `automind` |
| Open-ended Exploration | `deepanalyze`, `automind` |
| Quick Analysis | `data_interpreter` |
| Question Answering | `aide` |

You can override the recommendation by specifying `workflow` parameter.

## Migration from DSAT API

### Old Way (DSAT API)

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

### New Way (DSLighting API)

```python
import dslighting

result = dslighting.run_agent("data/competitions/titanic")
```

**Key Benefits:**
- 10x less code
- Auto-detects task types
- No async/await needed
- Sensible defaults

## Advanced Usage

### Access Underlying Components

```python
import dslighting

agent = dslighting.Agent()

# Access DSATConfig
config = agent.get_config()
config.llm.temperature = 0.5

# Access DSATRunner
runner = agent.get_runner()
eval_fn = runner.get_eval_function()
```

### Custom Output Path

```python
result = agent.run(
    data,
    output_path="my_submission.csv"
)
```

### Task ID and Description

```python
result = agent.run(
    data,
    task_id="my-experiment-001",
    description="Build a model to predict customer churn"
)
```

## Examples Directory

See `examples/dslighting_api/` for more examples:

- `example_1_basic.py` - Basic usage patterns
- `example_2_advanced.py` - Advanced features
- `example_3_migration.py` - Migration from DSAT API

## Backward Compatibility

The new DSLighting API is **fully backward compatible**:

- Existing DSAT code continues to work unchanged
- Both APIs can coexist in the same project
- DSLighting uses DSAT internally - no functionality loss

```python
# Use both APIs in the same project
import dslighting
from dsat.config import DSATConfig
from dsat.runner import DSATRunner

# Simple case - use DSLighting
agent = dslighting.Agent()
result = agent.run(data)

# Complex case - use DSAT directly
config = DSATConfig(...)
runner = DSATRunner(config)
```

## License

AGPL-3.0

### Installation Notes

The `dslighting` package is designed to work within the DSLighting environment. It relies on dependencies that are already installed via `requirements_local.txt`:

- **pandas** - Data manipulation
- **python-dotenv** - Environment variable loading
- **rich** - Beautiful terminal output (optional)
- All DSAT framework components

When you install with `pip install -e .`, it creates an entry point for the simplified API without re-installing these dependencies.

## More Information

- **Full Documentation**: https://luckyfan-cs.github.io/dslighting-web/
- **GitHub Repository**: https://github.com/usail-hkust/dslighting
- **Bug Reports**: https://github.com/usail-hkust/dslighting/issues
