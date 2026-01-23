<div align="center">

<img src="assets/dslighting.png" alt="DSLIGHTING Logo" width="180" style="border-radius: 15px;">

# DSLIGHTING: Full-Stack Data Science Workflow Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-2.7.9-blue?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/dslighting/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dslighting?style=flat-square&logo=pypi)](https://pypi.org/project/dslighting/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](LICENSE)

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/🚀-Quick_Start-green?style=for-the-badge" alt="Quick Start"></a>
  &nbsp;&nbsp;
  <a href="#core-features"><img src="https://img.shields.io/badge/⚡-Features-blue?style=for-the-badge" alt="Core Features"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/"><img src="https://img.shields.io/badge/📚-Docs-orange?style=for-the-badge" alt="Documentation"></a>
  &nbsp;&nbsp;
  <a href="https://luckyfan-cs.github.io/dslighting-web/guide/getting-started.html"><img src="https://img.shields.io/badge/📖-User_Guide-purple?style=for-the-badge" alt="User Guide"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge" alt="Stars"></a>
  &nbsp;&nbsp;
  <img src="https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge" alt="Profile views">
</p>

[🇨🇳 中文](README_CN.md) · [日本語](docs/README_JA.md) · [Français](docs/README_FR.md)

</div>

<div align="center">

🎯 **Intelligent Agent Workflows** &nbsp;•&nbsp; 📊 **Interactive Data Visualization**<br>
🤖 **Automated Code Generation** &nbsp;•&nbsp; 📈 **End-to-End Task Evaluation**

[⭐ Star us](https://github.com/usail-hkust/dslighting/stargazers) &nbsp;•&nbsp; [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## 📖 Overview

DSLIGHTING is a full-stack data science workflow system with agent-style workflows and a reusable data layout for task execution, evaluation, and iteration.

### ✨ Key Features

- 🤖 **Multiple Agent Workflows**: Integrated aide, automind, dsagent, and other intelligent agent styles
- 🔄 **Meta-Optimization Framework**: Support for AFlow meta-optimization to automatically select optimal workflows
- 📊 **Web Visualization Interface**: Interactive Dashboard based on Next.js + FastAPI
- 📝 **Complete Logging**: Records artifacts and summaries for each run
- 🧩 **Extensible Architecture**: Flexible task registry and data preparation flow
- 📦 **Smart Package Context** (v1.4.0+): Auto-detects available packages to avoid incompatible code
- 🎯 **Built-in Datasets** (v1.8.1+): Ready-to-run sample datasets with zero setup

---

## 🆕 Quick Experience

### Step 1: Install DSLighting

```bash
# Create a virtual environment (recommended)
python3 -m venv dslighting-env
source dslighting-env/bin/activate  # Windows: dslighting-env\Scripts\activate

# Install DSLighting
pip install dslighting
```

### Step 2: Configure API Keys

Create a `.env` file and set your keys:

```bash
# .env
API_KEY=sk-your-api-key-here
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

**Supported providers**:
- **OpenAI**: https://openai.com/ - API Base: `https://api.openai.com/v1`
- **Zhipu AI** (Recommended in China): https://bigmodel.cn/ - API Base: `https://open.bigmodel.cn/api/paas/v4`
- **SiliconFlow**: https://siliconflow.cn/ - API Base: `https://api.siliconflow.cn/v1`

### Step 3: Choose How to Use

---

**🌱 Beginner Mode (Recommended)**

#### Option 1: Built-in Dataset (Zero Setup)

**No data preparation required, run in one line!**

```python
# run_builtin.py
from dotenv import load_dotenv
load_dotenv()

import dslighting

# Use built-in dataset without configuring data paths
result = dslighting.run_agent(task_id="bike-sharing-demand")

print(f"✅ Done! Score: {result.score}")
```

**Built-in dataset**:
- `bike-sharing-demand` - Bike demand prediction
- ✅ Includes full train/test/answer files
- ✅ Ready to run out of the box
- ✅ Great for quick experience and testing

#### Option 2: Open-Ended API (Recommended for Beginners)

**Three major functions: analyze, process, model**

```python
import dslighting

# Analyze - explore data (2 iterations, keep workspace)
result = dslighting.analyze(
    data="./data/titanic",
    description="Analyze passenger distribution",
    model="gpt-4o"
)

# Process - clean data (3 iterations, keep workspace)
result = dslighting.process(
    data="./data/titanic",
    description="Handle missing values and outliers",
    model="gpt-4o"
)

# Model - train models (4 iterations, keep workspace)
result = dslighting.model(
    data="./data/titanic",
    description="Train a survival prediction model",
    model="gpt-4o"
)
```

**Highlights**:
- 🎯 **Simple and intuitive**: three APIs for common tasks
- 🔄 **Auto-iteration**: sensible defaults per task type
- 📁 **Result preservation**: workspace and outputs saved automatically

📖 **Full tutorial**: [examples/open_ended_demo/README.md](examples/open_ended_demo/README.md)

---

**🚀 Advanced Mode (For Power Users)**

#### Option 3: Global Configuration

**Configure once, reuse everywhere**

```python
import dslighting

# Configure data and registry directories
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

# Then only provide task_id
agent = dslighting.Agent()
result = agent.run(task_id="my-custom-task")
```

**Advanced mode benefits**:
- 🔧 **Centralized management** for multiple tasks
- 📊 **Batch processing** for many competitions
- ⚡ **Higher efficiency** with fewer repeated configs

#### Option 4: Define a Custom Agent (Expert Mode)

**Build your own Agent with full workflow control**

By defining **Operator**, **Workflow**, and **Factory**, you can build fully custom agents for complex tasks.

**Example: Build a custom Agent**

```python
from dslighting.operators.custom import SimpleOperator

# 1. Define an operator (reusable capability)
async def summarize(text: str) -> dict:
    return {"summary": text[:200]}

summarize_op = SimpleOperator(func=summarize, name="Summarize")

# 2. Define a workflow (chain operators)
class MyWorkflow:
    def __init__(self, operators):
        self.ops = operators

    async def solve(self, description, io_instructions, data_dir, output_path):
        _ = await self.ops["summarize"](text=description)

# 3. Create a factory (build the workflow)
class MyWorkflowFactory:
    def __init__(self, model="openai/gpt-4o"):
        self.model = model

    def create_agent(self):
        operators = {"summarize": summarize_op}
        return MyWorkflow(operators)

# 4. Use the custom Agent
agent = MyWorkflowFactory(model="openai/deepseek-ai/DeepSeek-V3.1-Terminus").create_agent()
```

**Core concepts**:
- **Operator**: reusable atomic capabilities (analysis, modeling, visualization)
- **Workflow**: chains operators to solve tasks
- **Factory**: builds and configures agents

**Use cases**:
- 🎯 Special task logic
- 🔬 Research on new agent architectures
- 🧩 Compose multiple specialized capabilities
- 📈 Optimize domain-specific workflows

**Best practices**:
- ✅ Keep outputs flexible: reports, charts, models
- ✅ Use sandboxed execution for safety
- ✅ Prefer small, composable operators

📖 **Full tutorial**: [AdvancedDSAgent examples](https://github.com/usail-hkust/dslighting/tree/main/examples/advanced_custom_agent)

---

## 🚀 Quick Start

### System Requirements

- **Python**: 3.10 or higher
  ```bash
  # Check Python version
  python --version
  # or
  python3 --version
  ```
- **Node.js**: 18.x or higher
  ```bash
  # Check Node.js version
  node --version
  ```
- **npm**: 9.x or higher (comes with Node.js)
  ```bash
  # Check npm version
  npm --version
  ```
- **Git**: For version control

### 1. Setup Environment

```bash
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting
python3.10 -m venv dslighting
source dslighting/bin/activate  # Windows: dslighting\Scripts\activate
```

### 2. Install Dependencies

**Standard installation** (recommended):
```bash
pip install -r requirements.txt
```

**Alternative option** (if standard installation fails):
```bash
pip install -r requirements_local.txt
```

> 💡 **Notes**:
> - `requirements.txt`: Locked versions, suitable for production environments
> - `requirements_local.txt`: Unlocked versions, more flexible dependencies, suitable for development

### 3. Configure API Keys

```bash
cp .env.example .env
# Edit .env file to set your API keys
```

DSLighting supports multiple LLM providers:

**Chinese Providers** (Recommended for users in China):
- **Zhipu AI** (https://bigmodel.cn/) - GLM series models
  - API Base: `https://open.bigmodel.cn/api/paas/v4`
  - Get keys: https://open.bigmodel.cn/usercenter/apikeys
- **SiliconFlow** (https://siliconflow.cn/) - DeepSeek, Qwen, etc.
  - API Base: `https://api.siliconflow.cn/v1`
  - Get keys: https://siliconflow.cn/account/ak

**International Providers**:
- **OpenAI** (https://openai.com/) - GPT series models
  - API Base: `https://api.openai.com/v1`
  - Get keys: https://platform.openai.com/api-keys

You can set `API_KEY`/`API_BASE` or provide per-model overrides via `LLM_MODEL_CONFIGS`.

> 💡 **Configuration Examples**: Check `.env.example` file for detailed multi-model configuration examples, including API key rotation, temperature settings, etc.

### 4. Prepare Data

DSLighting supports multiple data sources. Choose any of the following methods:

#### Method 1: Download via MLE-Bench (Recommended)

[MLE-Bench](https://github.com/openai/mle-bench) is a machine learning evaluation benchmark provided by OpenAI.

```bash
# 1. Clone MLE-Bench repository
git clone https://github.com/openai/mle-bench.git
cd mle-bench

# 2. Install dependencies
pip install -e .

# 3. Download all datasets
python scripts/prepare.py --competition all

# 4. Link data to DSLighting project
# MLE-Bench data is downloaded to ~/mle-bench/data/
# Create symlink or copy to dslighting project
ln -s ~/mle-bench/data/competitions /path/to/dslighting/data/competitions
```

> 📖 **More Info**: Visit [MLE-Bench GitHub](https://github.com/openai/mle-bench) for complete dataset list.

#### Method 2: Custom Dataset

Organize your data according to DSLighting's data layout:

```
data/competitions/
  <competition-id>/
    config.yaml           # Competition config
    prepared/
      public/            # Public data (train, sample)
      private/           # Private data (test labels)
```

> 💡 **Note**: More data types and pretrained models will be supported soon. Stay tuned!

> 📖 **Data preparation guide**: See [DATA_PREPARATION.md](DATA_PREPARATION.md) for details.

### 5. Run a Single Task

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand \
  --llm-model gpt-4
```

### 6. Interactive Web UI (Recommended)

We provide a Next.js + FastAPI web interface for easier data upload and task execution.

#### 📸 Web UI Preview

**Main Dashboard**
![Main Dashboard](assets/web_ui_main_page.png)

**Exploratory Data Analysis (EDA)**
![EDA](assets/web_ui_eda.png)

**Custom Tasks**
![Custom Tasks](assets/web_ui_user_custome_task.png)

**Model Training**
![Model Training](assets/web_ui_model_training.png)

**Report Generation**
![Report Generation](assets/web_ui_report.png)

#### 6.1 Backend Setup

The backend depends on the main dslighting environment, only requiring additional web framework dependencies:

```bash
source dslighting/bin/activate
# Install backend dependencies
pip install -r web_ui/backend/requirements.txt
```

#### 6.2 Start the Backend

```bash
# Enter backend directory
cd web_ui/backend

# Start backend (default port 8003)
python main.py
```

Or use uvicorn directly:

```bash
cd web_ui/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

> 📖 **Documentation**: See [Backend README](web_ui/backend/README.md) for API endpoints and configuration

> 💡 **Tip**: The backend runs on port **8003** by default. If the port is occupied, modify the port in `main.py`.

#### 6.3 Start the Frontend

```bash
cd web_ui/frontend
npm install   # Install dependencies (first time only)
npm run dev   # Start the development server
```

> 📖 **Documentation**: See [Frontend README](web_ui/frontend/README.md) for more frontend development details

#### 6.4 Access the Dashboard

Open your browser and navigate to: [http://localhost:3000](http://localhost:3000)

---

## 🏗️ Core Features

### Agent Workflows

- **`aide`**: Iterative code generation and review loop
- **`automind`**: Planning + reasoning with memory and decomposition
- **`dsagent`**: Plan/execute loop with structured operator flow
- **`data_interpreter`**: Fast loop for code execution and debugging
- **`autokaggle`**: SOP-style Kaggle workflow
- **`aflow`**: Meta-optimization over workflows
- **`deepanalyze`**: Analysis-focused execution workflow

### Data Layout

```
data/competitions/
  <competition-id>/
    config.yaml           # Competition config
    prepared/
      public/            # Public data
      private/           # Private data
```

### Configuration

`config.yaml` is read by the benchmark runners and the LLM service:

- `competitions`: default competition list for MLEBench
- `sciencebench_competitions` (optional): default list for ScienceBench
- `custom_model_pricing`: per-model token pricing overrides for LiteLLM
- `run`: trajectory logging toggles

### Custom Model Pricing

**Default behavior**:
- DSLighting uses LiteLLM's built-in default pricing
- If `config.yaml` is missing, the system still works (no error)
- Pricing config is optional and only needed to override defaults

**Custom pricing**:

If you need custom pricing for specific models, create a `config.yaml` in your project directory:

**Locations**:
```bash
# For pip installation
/path/to/your/project/config.yaml

# Example in a test project
/Users/liufan/Applications/Github/dslighting_test_project/config.yaml
```

> 📖 **Reference example**: See [config.yaml.example](config.yaml.example) for a full example

**Example**:
```yaml
custom_model_pricing:
  openai/Qwen/Qwen3-Coder-480B-A35B-Instruct:
    input_cost_per_token: 6.0e-07
    output_cost_per_token: 1.8e-06
  openai/Qwen/Qwen3-Coder-30B-A3B-Instruct:
    input_cost_per_token: 6.0e-07
    output_cost_per_token: 1.8e-06
  o4-mini-2025-04-16:
    input_cost_per_token: 1.1e-06
    output_cost_per_token: 4.4e-06
  openai/deepseek-ai/DeepSeek-V3.1-Terminus:
    input_cost_per_token: 5.55e-07
    output_cost_per_token: 1.67e-06
```

**Parameters**:
- `input_cost_per_token`: input token price (per request)
- `output_cost_per_token`: output token price (per response)
- Unit: USD/token (scientific notation is common)

**Notes**:
- 💡 Pricing config is optional; missing config does not error
- 💡 Only override models you need; others use defaults
- 💡 Pricing affects cost calculation and budget control

---

## 📂 Logs and Artifacts

By default, logs are written to:

```
runs/benchmark_results/<workflow>_on_<benchmark>/<model_name>/
```

You can override the base directory with `--log-path`.

---

## ❓ FAQ

See `FAQ.md` for more information.

---

## ⭐ Star History

<div align="center">

[![Stargazers repo roster for @usail-hkust/dslighting](https://reporoster.com/stars/usail-hkust/dslighting)](https://github.com/usail-hkust/dslighting/stargazers)

[![Forkers repo roster for @usail-hkust/dslighting](https://reporoster.com/forks/usail-hkust/dslighting)](https://github.com/usail-hkust/dslighting/network/members)

[![Star History Chart](https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=Date)](https://star-history.com/#usail-hkust/dslighting&Date)

</div>

---

## 💬 WeChat Community

Join our WeChat group to connect with other users and developers!

<div align="center">

<img src="assets/wechat_group.jpg" alt="WeChat Group" width="300" style="border-radius: 10px; border: 2px solid #e0e0e0;">

**Scan the QR code above to join the DSLighting user community**

</div>

In the group, you can:
- 🤝 Connect with other users and share experiences
- 💡 Suggest features and provide feedback
- 🐛 Report bugs and get help
- 📢 Stay updated with the latest development news

---

## 🤝 Contributing

<div align="center">

We hope DSLIGHTING could become a gift for the community. 🎁

<a href="https://github.com/usail-hkust/dslighting/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=usail-hkust/dslighting" />
</a>

**Core Contributors**:
- [luckyfan-cs](https://github.com/luckyfan-cs) (project lead, frontend & backend development)
- [canchengliu](https://github.com/canchengliu) (workflow contribution)

See `CONTRIBUTING.md` for details.

</div>

---

## 🔗 Community

<div align="center">

**[DSLIGHTING Community](https://github.com/luckyfan-cs)**

[💬 WeChat Group](#-wechat-community) · [⭐ Star us](https://github.com/usail-hkust/dslighting/stargazers) · [🐛 Report a bug](https://github.com/usail-hkust/dslighting/issues) · [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## 📄 License

This project is licensed under the AGPL-3.0 License.

---

## 🙏 Thanks

Thank you for visiting DSLIGHTING!

---

## 📊 Project Statistics

![](https://komarev.com/ghpvc/?username=usail-hkust&repo=dslighting&style=for-the-badge)
![](https://img.shields.io/github/issues/usail-hkust/dslighting?style=for-the-badge)
![](https://img.shields.io/github/forks/usail-hkust/dslighting?style=for-the-badge)
![](https://img.shields.io/github/stars/usail-hkust/dslighting?style=for-the-badge)

---

## 📚 Citation

If you use DSLIGHTING in your research, please cite:

```bibtex
@software{dslighting2025,
  title = {DSLIGHTING: An End-to-End Data Science Intelligent Assistant System},
  author = {Liu, F. and Liu, C. and others},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/usail-hkust/dslighting},
  version = {1.0.0}
}
```

Or in plain text:

```
Liu, F., Liu, C., et al. (2025). DSLIGHTING: An End-to-End Data Science Intelligent Assistant System.
GitHub repository. https://github.com/usail-hkust/dslighting
```
