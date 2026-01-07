<div align="center">

# DSLIGHTING 中文说明

个性化数学科学专家助理，强调全流程数据科学实践与落地。

[快速开始](#快速开始) · [工作流](#工作流) · [数据结构](#数据结构) · [配置说明](#配置说明) · [English](../README.md) · [日本語](README_JA.md) · [Français](README_FR.md)

</div>

## 简介

DSLIGHTING 提供统一的任务入口、可扩展的工作流实现与标准化数据目录结构，
覆盖数据准备、建模、评估到结果沉淀的完整流程。

## 主要特性

- 统一 CLI 入口，支持多种工作流模式
- 可复用的工作流实现（AIDE、AutoMind、DSAgent、AFlow 等）
- 自动化日志与结果归档
- 可扩展的任务注册与数据准备流程

## 工作流

- `aide`: 生成-执行-审阅循环
- `automind`: 规划 + 记忆 + 分解
- `dsagent`: 结构化计划/执行流程
- `data_interpreter`: 快速执行与调试
- `autokaggle`: SOP 风格 Kaggle 流程
- `aflow`: 工作流元优化
- `deepanalyze`: 分析导向执行

## 快速开始

### 1. 环境准备

```bash
git clone <repository_url>
cd dslighting
python -m venv dsat
source dsat/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
cp .env.example .env
```

### 4. 准备数据

将准备好的比赛数据放在数据目录下，结构参考下方“数据结构”。

### 5. 运行示例

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --data-dir data/competitions \
  --task-id bike-sharing-demand
```

## 数据结构

```
data/competitions/
  <competition-id>/
    config.yaml
    prepared/
      public/
      private/
```

ScienceBench 使用同样的目录结构。

## 配置说明

项目根目录的 `config.yaml` 会被读取，用于：

- `competitions`: MLEBench 默认任务列表
- `sciencebench_competitions`: ScienceBench 默认任务列表
- `custom_model_pricing`: LiteLLM 模型计价覆盖
- `run`: 轨迹日志相关配置

## 日志与输出

默认输出路径：

```
runs/benchmark_results/<workflow>_on_<benchmark>/<model_name>/
```

可用 `--log-path` 自定义。

---

[返回英文说明](../README.md)
