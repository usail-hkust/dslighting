<div align="center">

<img src="../assets/dslighting.png" alt="DSLIGHTING Logo" width="180" style="border-radius: 15px;">

# DSLIGHTING: Full-Stack Data Science Workflow Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](../LICENSE)

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/🚀-Quick_Start-green?style=for-the-badge" alt="Quick Start"></a>
  &nbsp;&nbsp;
  <a href="#core-features"><img src="https://img.shields.io/badge/⚡-Features-blue?style=for-the-badge" alt="Core Features"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/issues"><img src="https://img.shields.io/badge/📚-Docs-orange?style=for-the-badge" alt="Documentation"></a>
</p>

[🇨🇳 中文](../README.md) · [日本語](README_JA.md) · [Français](README_FR.md)

</div>

<div align="center">

🎯 **Intelligent Agent Workflows** &nbsp;•&nbsp; 📊 **Interactive Data Visualization**<br>
🤖 **Automated Code Generation** &nbsp;•&nbsp; 📈 **End-to-End Task Evaluation**

[⭐ Star us](https://github.com/usail-hkust/dslighting/stargazers) &nbsp;•&nbsp; [💬 Discussions](https://github.com/usail-hkust/dslighting/discussions)

</div>

---

## 📸 Web UI Preview

### Main Dashboard
![Main Dashboard](../assets/web_ui_main_page.png)

### Exploratory Data Analysis (EDA)
![EDA](../assets/web_ui_eda.png)

### Custom Tasks
![Custom Tasks](../assets/web_ui_user_custome_task.png)

### Model Training
![Model Training](../assets/web_ui_model_training.png)

### Report Generation
![Report Generation](../assets/web_ui_report.png)

---

## 📖 Overview

DSLIGHTING is a full-stack data science workflow system with agent-style workflows and a reusable data layout for task execution, evaluation, and iteration.

### ✨ Key Features

- 🤖 **Multiple Agent Workflows**: Integrated aide, automind, dsagent, and other intelligent agent styles
- 🔄 **Meta-Optimization Framework**: Support for AFlow meta-optimization to automatically select optimal workflows
- 📊 **Web Visualization Interface**: Interactive Dashboard based on Next.js + FastAPI
- 📝 **Complete Logging**: Records artifacts and summaries for each run
- 🧩 **Extensible Architecture**: Flexible task registry and data preparation flow

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

**International Providers**:
- **OpenAI** (https://openai.com/) - GPT series models
  - API Base: `https://api.openai.com/v1`
  - Get keys: https://platform.openai.com/api-keys

**Chinese Providers** (Recommended for users in China):
- **Zhipu AI** (https://bigmodel.cn/) - GLM series models
  - API Base: `https://open.bigmodel.cn/api/paas/v4`
  - Get keys: https://open.bigmodel.cn/usercenter/apikeys
- **SiliconFlow** (https://siliconflow.cn/) - DeepSeek, Qwen, etc.
  - API Base: `https://api.siliconflow.cn/v1`
  - Get keys: https://siliconflow.cn/account/ak

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

### 5. Run a Single Task

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand
```

### 6. Interactive Web UI (Recommended)

We provide a Next.js + FastAPI web interface for easier data upload and task execution.

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

> 📖 **Documentation**: See [Backend README](../../web_ui/backend/README.md) for API endpoints and configuration

> 💡 **Tip**: The backend runs on port **8003** by default. If the port is occupied, modify the port in `main.py`.

#### 6.3 Start the Frontend

```bash
cd web_ui/frontend
npm install   # Install dependencies (first time only)
npm run dev   # Start the development server
```

> 📖 **Documentation**: See [Frontend README](../../web_ui/frontend/README.md) for more frontend development details

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

<p>
  <a href="https://github.com/usail-hkust/dslighting/stargazers"><img src="../assets/roster/stargazers.svg" alt="Stargazers"/></a>
  &nbsp;&nbsp;
  <a href="https://github.com/usail-hkust/dslighting/network/members"><img src="../assets/roster/forkers.svg" alt="Forkers"/></a>
</p>

<a href="https://www.star-history.com/#usail-hkust/dslighting&type=timeline&legend=top-left">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&theme=dark&legend=top-left" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&legend=top-left" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=usail-hkust/dslighting&type=timeline&legend=top-left" />
  </picture>
</a>

</div>

---

## 💬 WeChat Community

Join our WeChat group to connect with other users and developers!

<div align="center">

<img src="../assets/wechat_group.jpg" alt="WeChat Group" width="300" style="border-radius: 10px; border: 2px solid #e0e0e0;">

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
