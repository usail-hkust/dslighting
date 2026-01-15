# 快速开始

DSLIGHTING 是一个全流程数据科学智能助手系统，采用 Agent 式工作流和可复用的数据布局，为数据科学任务提供端到端的执行、评估和迭代能力。

## 系统要求

- **Python**: 3.10 或更高版本
- **Node.js**: 18.x 或更高版本
- **npm**: 9.x 或更高版本
- **Git**: 用于版本控制

## 安装步骤

### 1. 克隆仓库

\`\`\`bash
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting
\`\`\`

### 2. 创建虚拟环境

\`\`\`bash
python3.10 -m venv dslighting
source dslighting/bin/activate  # Windows: dslighting\\Scripts\\activate
\`\`\`

### 3. 安装依赖

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. 配置 API 密钥

\`\`\`bash
cp .env.example .env
# 编辑 .env 文件，设置你的 API 密钥
\`\`\`

DSLighting 支持多种 LLM 提供商：

- **智谱AI** (GLM系列)
- **硅基流动** (DeepSeek、Qwen等)
- **OpenAI** (GPT系列)

### 5. 准备数据

使用 [MLE-Bench](https://github.com/openai/mle-bench) 数据集：

\`\`\`bash
git clone https://github.com/openai/mle-bench.git
cd mle-bench
pip install -e .
python scripts/prepare.py --competition all
\`\`\`

### 6. 运行任务

\`\`\`bash
python run_benchmark.py \\
  --workflow aide \\
  --benchmark mle \\
  --data-dir data/competitions \\
  --task-id bike-sharing-demand \\
  --llm-model gpt-4
\`\`\`

## 使用 Web UI

我们还提供了现代化的 Web 界面：

### 启动后端

\`\`\`bash
cd web_ui/backend
pip install -r requirements.txt
python main.py
\`\`\`

### 启动前端

\`\`\`bash
cd web_ui/frontend
npm install
npm run dev
\`\`\`

访问 [http://localhost:3000](http://localhost:3000) 查看界面。

## 下一步

- 了解[核心功能](/guide/features)
- 查看[数据准备指南](/guide/data-preparation)
- 阅读[配置说明](/guide/configuration)
