# API 文档概览

DSLIGHTING 提供了丰富的 API 接口，支持灵活的任务配置和执行。

## 核心 API

### Benchmark API

运行基准测试的主要接口。

\`\`\`python
python run_benchmark.py \\
  --workflow <workflow_name> \\
  --benchmark <benchmark_name> \\
  --data-dir <path_to_data> \\
  --task-id <task_id> \\
  --llm-model <model_name>
\`\`\`

### Agent API

各个 Agent 工作流的接口和配置。

### Web API

Web UI 的 REST API 接口。

## 快速链接

- [Agent 工作流 API](/api/agents)
- [Benchmark API](/api/benchmark)
- [Web API](#) (待补充)

## 参数说明

### 通用参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| \`--workflow\` | string | Agent 工作流名称 | aide |
| \`--benchmark\` | string | 基准测试名称 | mle |
| \`--data-dir\` | path | 数据目录路径 | data/competitions |
| \`--llm-model\` | string | LLM 模型名称 | gpt-4 |
| \`--log-path\` | path | 日志输出路径 | runs/benchmark_results |
| \`--max-workers\` | int | 最大并发数 | 1 |

### 工作流特定参数

每个工作流都有其特定的参数配置，详见各工作流文档。

查看详细 API 文档：
- [Agent 工作流 API](/api/agents)
- [Benchmark API](/api/benchmark)
