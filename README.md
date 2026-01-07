<div align="center">

<img src="assets/dslighting.png" alt="DSLIGHTING Logo" width="180">

# DSLIGHTING

Personalized math and science expert assistant, built as a full-stack data science workflow runner. Personalized 数据科学专家

[Quick Start](#quick-start) · [Workflows](#workflows) · [Data Layout](#data-layout) · [Configuration](#configuration) · [中文说明](docs/README_CN.md) · [日本語](docs/README_JA.md) · [Français](docs/README_FR.md)

</div>

## Overview

DSLIGHTING is a full-process data science workflow system with agent-style workflows and a
repeatable data layout for task execution, evaluation, and iteration.

## Key Features

- Unified CLI runner for end-to-end data science workflows
- Workflow implementations for different agent styles and meta-optimization (AFlow)
- Run logging with per-run artifacts and summaries
- Extensible task registry and data preparation flow

## Workflows

- `aide`: iterative code generation and review loop
- `automind`: planning + reasoning with memory and decomposition
- `dsagent`: plan/execute loop with structured operator flow
- `data_interpreter`: fast loop for code execution and debugging
- `autokaggle`: SOP-style Kaggle workflow
- `aflow`: meta-optimization over workflows
- `deepanalyze`: analysis-focused execution workflow

## Quick Start

### 1. Setup Environment

```bash
git clone <repository_url>
cd dslighting
python -m venv dsat
source dsat/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
cp .env.example .env
```

You can set `API_KEY`/`API_BASE` or provide per-model overrides via `LLM_MODEL_CONFIGS`.

### 4. Prepare Data

See the expected layout below. Place prepared competitions under your data directory.

### 5. Run a Single Task

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand
```

### 6. Use Provided Single-Task Scripts

Each agent has one sample script under `job_scripts/<agent>/`.
Update the `DATA_DIR` in the script to point at your prepared competitions root if needed.

## Data Layout

Expected data structure:

```
data/competitions/
  <competition-id>/
    config.yaml
    prepared/
      public/
      private/
```

For ScienceBench, the layout follows the same structure.

## Configuration

`config.yaml` is read by the benchmark runners and the LLM service:

- `competitions`: default competition list for MLEBench
- `sciencebench_competitions` (optional): default list for ScienceBench
- `custom_model_pricing`: per-model token pricing overrides for LiteLLM
- `run`: trajectory logging toggles

## Logs and Artifacts

By default, logs are written to:

```
runs/benchmark_results/<workflow>_on_<benchmark>/<model_name>/
```

You can override the base directory with `--log-path`.

## FAQ

See `docs/FAQ.md`.

## Star History

| Stargazers | Forkers |
| --- | --- |
| TBD | TBD |

Star History Chart: add chart under `assets/` and link it here.

## Contribution

We hope DSLIGHTING can become a gift for the community. 🎁
See `docs/CONTRIBUTING.md`.

## Community

⭐ Star us · 🐛 Report a bug · 💬 Discussions

## License

This project is licensed under the AGPL-3.0 License.

## Thanks

✨ Thanks for visiting DSLIGHTING!

## Views

TBD
