<div align="center">

# DSLighting

**End-to-End Data Science Agent**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-2.7.9-blue?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/dslighting/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dslighting?style=flat-square&logo=pypi)](https://pypi.org/project/dslighting/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](https://github.com/usail-hkust/dslighting/blob/main/LICENSE)

[📚 Full Docs](https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html) |
[🚀 Quick Start](#-quick-start) |
[💻 GitHub](https://github.com/usail-hkust/dslighting) |
[🐛 Issues](https://github.com/usail-hkust/dslighting/issues)

</div>

---

## ✨ Highlights

- 🤖 **Intelligent Agent Workflows**: aide / automind / dsagent / data_interpreter / autokaggle / aflow, etc.
- 🔍 **Discovery API**: explore all available prompts and operators
- 📊 **Data Management**: unified data loading, task registry, and grading
- 🔧 **Multi-model Support**: OpenAI, GLM, DeepSeek, Qwen, and more
- 🧩 **Extensible Architecture**: custom tasks, workflows, and operators
- 📦 **Smart Package Context**: auto-detect installed packages to avoid incompatible code
- 🎯 **Built-in Datasets**: run demos without data preparation
- 📝 **Full Traceability**: logs, workspace, and artifacts saved automatically

---

## 🚀 Quick Start

### 1. Install

```bash
pip install dslighting python-dotenv
```

**System requirements**: Python 3.10+. Using a virtual environment is recommended.

#### 🍎 macOS note (xgboost)

If you use **xgboost**, install the OpenMP runtime:

```bash
brew install libomp
```

Otherwise you may see `XGBoostError: Library not loaded: libomp.dylib`.

---

### 2. Configure environment variables

Create a `.env` file:

```bash
# .env

# Default model (required)
LLM_MODEL=glm-4

# Multi-model config (JSON)
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

**Supported providers**:
- OpenAI (GPT-4 / GPT-3.5)
- Zhipu AI (GLM-4)
- SiliconFlow (DeepSeek / Qwen / Kimi, etc.)
- Any OpenAI-compatible API

> 💡 **Tip**: call `load_dotenv()` before importing `dslighting`.

---

## 🆕 Quick Experience

### Option 1: Built-in dataset (zero setup)

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# No data prep required
result = dslighting.run_agent(task_id="bike-sharing-demand")
print(f"✅ Done! Score: {result.score}")
```

Built-in dataset example:
- `bike-sharing-demand` (bike demand forecasting)

### Option 2: Open-ended API (recommended for beginners)

```python
import dslighting

# Analyze
result = dslighting.analyze(
    data="./data/titanic",
    description="Analyze passenger distribution",
    model="gpt-4o"
)

# Process
result = dslighting.process(
    data="./data/titanic",
    description="Clean missing values and outliers",
    model="gpt-4o"
)

# Model
result = dslighting.model(
    data="./data/titanic",
    description="Train a survival prediction model",
    model="gpt-4o"
)
```

### Option 3: Global config (recommended for multi-task)

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# Configure once, reuse everywhere
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

agent = dslighting.Agent()
result = agent.run(task_id="bike-sharing-demand")
```

---

## 🌱 Beginner Usage

### 1. One-line demo (built-in dataset)

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

result = dslighting.run_agent(task_id="bike-sharing-demand")
print(f"✅ Done! Score: {result.score}")
```

### 2. Open-ended API trio (Analyze / Process / Model)

```python
import dslighting

# Analyze
_ = dslighting.analyze(
    data="./data/titanic",
    description="Analyze passenger distribution",
    model="gpt-4o"
)

# Process
_ = dslighting.process(
    data="./data/titanic",
    description="Handle missing values and outliers",
    model="gpt-4o"
)

# Model
_ = dslighting.model(
    data="./data/titanic",
    description="Train a survival prediction model",
    model="gpt-4o"
)
```

### 3. Check results and workspace

```python
print(result.workspace_path)
print(result.score)
```

---

## 🚀 Advanced Usage

### 1. Global config + reusable execution

```python
import dslighting

# Configure once, reuse
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    max_iterations=5,
    keep_workspace=True
)

result = agent.run(task_id="bike-sharing-demand")
```

### 2. Custom task registry (competition-style)

```python
result = agent.run(
    task_id="your-task-name",
    data_dir="/path/to/data/competitions",
    registry_dir="/path/to/registry"
)
```

### 3. Custom Agent (Operator / Workflow / Factory)

```python
from dslighting.operators.custom import SimpleOperator

async def summarize(text: str) -> dict:
    return {"summary": text[:200]}

summarize_op = SimpleOperator(func=summarize, name="Summarize")

class MyWorkflow:
    def __init__(self, operators):
        self.ops = operators

    async def solve(self, description, io_instructions, data_dir, output_path):
        _ = await self.ops["summarize"](text=description)

class MyWorkflowFactory:
    def __init__(self, model="openai/gpt-4o"):
        self.model = model

    def create_agent(self):
        return MyWorkflow({"summarize": summarize_op})

agent = MyWorkflowFactory().create_agent()
```

---

## 📦 Data Preparation

### Method 1: MLE-Bench (recommended)

```bash
git clone https://github.com/openai/mle-bench.git
cd mle-bench
pip install -e .
python scripts/prepare.py --competition all

# Link data to DSLighting
ln -s ~/mle-bench/data/competitions /path/to/dslighting/data/competitions
```

### Method 2: Custom dataset

```
data/competitions/
  <competition-id>/
    config.yaml
    prepared/
      public/
      private/
```

More details:
- https://github.com/usail-hkust/dslighting/blob/main/docs/DATA_PREPARATION.md

---

## 🧭 Discovery API (Explore Components)

```python
import dslighting

# List all prompts / operators
dslighting.explore()
```

List specific categories:

```python
all_prompts = dslighting.list_prompts()
llm_ops = dslighting.list_operators(category="llm")
```

Get details:

```python
from dslighting.prompts import get_prompt_info
from dslighting.operators import get_operator_info

print(get_prompt_info("create_improve_prompt"))
print(get_operator_info("PlanOperator"))
```

Full guide:
- https://github.com/usail-hkust/dslighting/blob/main/PIP_DOC/DISCOVERY_API_GUIDE.md

---

## 🧰 CLI Usage

After installation:

```bash
dslighting --help
```

Common subcommands:
- `dslighting help`: help and quick guide
- `dslighting workflows`: list all workflows
- `dslighting example <workflow>`: show workflow examples
- `dslighting quickstart`: detailed quick start
- `dslighting detect-packages`: detect packages and write to config.yaml
- `dslighting show-packages`: show detected packages
- `dslighting validate-config`: validate configuration

---

## 🔧 Custom Tasks (Advanced)

```
your-project/
├── data/competitions/
│   └── your-task-name/
│       └── prepared/
│           ├── public/
│           └── private/
└── registry/
    └── your-task-name/
        ├── config.yaml
        ├── description.md
        └── grade.py
```

Example `config.yaml`:

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
  name: rmsle  # or accuracy, f1, mae, etc.
```

Run a custom task:

```python
result = agent.run(
    task_id="your-task-name",
    data_dir="/path/to/data/competitions",
    registry_dir="/path/to/registry"
)
```

---

## 📈 Checking Results

```python
print(f"Workspace: {result.workspace_path}")
print(f"Score: {result.score}")
print(f"Cost: {result.cost}")
```

---

## 🧪 Web UI (Optional)

The Web UI requires the frontend/backend source. If you installed via pip, clone the repo:

```bash
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting
```

Backend:
```bash
pip install -r web_ui/backend/requirements.txt
cd web_ui/backend
python main.py
```

Frontend:
```bash
cd web_ui/frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

---

## 🎉 Latest Version: 2.7.9

**Highlights**:
- Comprehensive PyPI README with detailed documentation
- Enhanced installation guide with system requirements
- Multi-provider API setup examples (OpenAI, GLM, DeepSeek)
- Beginner and advanced usage examples
- Custom Agent tutorial for expert users
- Complete CLI and Web UI documentation

---

## 📚 Docs

- Quick Start: https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html
- Data System: https://luckyfan-cs.github.io/dslighting-web/api/data-system.html
- GitHub: https://github.com/usail-hkust/dslighting
- PyPI: https://pypi.org/project/dslighting/

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under [AGPL-3.0](https://github.com/usail-hkust/dslighting/blob/main/LICENSE).

---

<div align="center">

**If this project helps you, please give it a ⭐️**

Made with ❤️ by [USAIL Lab](https://github.com/usail-hkust)

</div>
