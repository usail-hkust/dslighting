# Benchmark API

基准测试 API 提供了灵活的任务配置和执行接口。

## run_benchmark.py

主入口脚本，用于运行各种基准测试任务。

### 基本用法

\`\`\`bash
python run_benchmark.py [OPTIONS]
\`\`\`

### 命令行参数

#### 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `--workflow` | string | Agent 工作流名称 |
| `--benchmark` | string | 基准测试名称 |
| `--data-dir` | path | 数据目录路径 |
| `--task-id` | string | 任务ID |

#### 可选参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `--llm-model` | string | LLM 模型名称 | gpt-4 |
| `--log-path` | path | 日志输出路径 | runs/benchmark_results |
| `--max-workers` | int | 最大并发任务数 | 1 |
| `--temperature` | float | LLM 温度参数 | 0.7 |

### 使用示例

#### 运行单个任务

\`\`\`bash
python run_benchmark.py \\
  --workflow aide \\
  --benchmark mle \\
  --data-dir data/competitions \\
  --task-id bike-sharing-demand
\`\`\`

#### 运行多个任务

\`\`\`bash
python run_benchmark.py \\
  --workflow dsagent \\
  --max-workers 3
\`\`\`

## 支持的基准测试

### MLE-Bench

OpenAI 的机器学习评估基准。

\`\`\`bash
python run_benchmark.py \\
  --workflow aide \\
  --benchmark mle \\
  --data-dir benchmarks/mlebench/competitions
\`\`\`

### Kaggle

支持各种 Kaggle 竞赛。

\`\`\`bash
python run_benchmark.py \\
  --workflow autokaggle \\
  --benchmark kaggle
\`\`\`

### 自定义任务

使用自己的数据集。

\`\`\`bash
python run_benchmark.py \\
  --workflow dsagent \\
  --benchmark custom
\`\`\`

## 输出格式

### 日志结构

\`\`\`
runs/benchmark_results/
  workflow_on_benchmark/
    model_name/
      task_id/
        config.json
        trace.json
        submission.csv
        report.md
        artifacts/
\`\`\`

### 评估指标

- **分类任务**: accuracy, F1-score, AUC
- **回归任务**: RMSE, MAE, R²
- **排名任务**: NDCG, MRR

[返回 API 概览](/api/overview)
