# 配置说明

DSLighting 通过配置文件和环境变量进行灵活配置。

## 环境变量配置

在项目根目录创建 \`.env\` 文件：

\`\`\`bash
# LLM API 配置
API_KEY=your_api_key_here
API_BASE=https://api.openai.com/v1

# 或使用多模型配置
LLM_MODEL_CONFIGS=[{"model": "gpt-4", "api_key": "key1", "api_base": "base1"}]

# 其他配置
LOG_PATH=runs/benchmark_results
MAX_WORKERS=4
\`\`\`

## LLM 提供商配置

### OpenAI

\`\`\`bash
API_KEY=sk-xxx
API_BASE=https://api.openai.com/v1
\`\`\`

### 智谱AI (推荐)

\`\`\`bash
API_KEY=your_zhipu_api_key
API_BASE=https://open.bigmodel.cn/api/paas/v4
\`\`\`

### 硅基流动

\`\`\`bash
API_KEY=your_siliconflow_api_key
API_BASE=https://api.siliconflow.cn/v1
\`\`\`

## config.yaml 配置

主配置文件 \`config.yaml\` 包含以下部分：

### Competitions 配置

\`\`\`yaml
competitions:
  - bike-sharing-demand
  - titanic
  - house-prices
\`\`\`

### 模型定价配置

\`\`\`yaml
custom_model_pricing:
  gpt-4:
    input: 0.03
    output: 0.06
  gpt-3.5-turbo:
    input: 0.0015
    output: 0.002
\`\`\`

### 日志配置

\`\`\`yaml
run:
  log_artifacts: true
  log_traces: true
  save_code: true
\`\`\`

## 工作流配置

每个工作流都可以有独立的配置：

### AIDE 配置

\`\`\`yaml
aide:
  max_iterations: 10
  temperature: 0.7
  review_threshold: 0.8
\`\`\`

### DSAgent 配置

\`\`\`yaml
dsagent:
  max_steps: 20
  planning_iterations: 3
  execution_timeout: 300
\`\`\`

## 运行时参数

通过命令行参数覆盖配置：

\`\`\`bash
python run_benchmark.py \\
  --workflow aide \\
  --llm-model gpt-4 \\
  --temperature 0.8 \\
  --max-iterations 15
\`\`\`

## Web UI 配置

Web UI 的配置文件位于 \`web_ui/backend/.env\`：

\`\`\`bash
# 后端配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8003
CORS_ORIGINS=http://localhost:3000

# 前端配置
NEXT_PUBLIC_API_URL=http://localhost:8003
\`\`\`

查看[常见问题](/guide/faq)解决配置问题。
