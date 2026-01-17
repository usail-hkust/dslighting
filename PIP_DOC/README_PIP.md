<div align="center">

# DSLighting

**全流程数据科学智能助手 - End-to-End Data Science Agent**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/PyPI-1.8.2-blue?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/dslighting/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dslighting?style=flat-square&logo=pypi)](https://pypi.org/project/dslighting/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](LICENSE)

[📚 完整文档](https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html) |
[🚀 快速上手](#-快速上手) |
[💻 GitHub](https://github.com/usail-hkust/dslighting) |
[🐛 问题反馈](https://github.com/usail-hkust/dslighting/issues)

</div>

---

## ✨ 特性

- 🤖 **智能 Agent 工作流**：自动化数据科学任务执行
- 📊 **数据管理**：统一的数据加载和任务配置系统
- 🔧 **灵活配置**：支持多种 LLM 模型（OpenAI, GLM, DeepSeek, Qwen 等）
- 📝 **完整追踪**：自动记录任务执行过程和结果
- 🧩 **可扩展架构**：轻松添加自定义任务和工作流

---

## 🚀 快速上手

### 1. 安装

```bash
pip install dslighting python-dotenv
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# .env

# 指定默认使用的模型（必须设置！）
LLM_MODEL=glm-4

# 多模型配置（JSON 格式）
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

**支持的模型提供商：**
- OpenAI (GPT-4, GPT-3.5)
- 智谱 AI (GLM-4)
- SiliconFlow (DeepSeek, Qwen, Kimi 等)
- 任何兼容 OpenAI API 的服务

### 3. 运行任务

**方式 1：全局配置（推荐用于多任务）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 配置一次，全局生效
dslighting.setup(
    data_parent_dir="/path/to/data/competitions",
    registry_parent_dir="/path/to/registry"
)

# 创建 Agent
agent = dslighting.Agent()

# 运行任务（只需 task_id）
result = agent.run(task_id="bike-sharing-demand")

print(f"✅ 任务完成！")
print(f"结果: {result}")
```

**方式 2：直接路径（明确清晰）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

agent = dslighting.Agent()
result = agent.run(
    task_id="bike-sharing-demand",
    data_dir="/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)
```

**方式 3：内置数据集（最简单）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 无需配置，直接使用
result = dslighting.run_agent(task_id="bike-sharing-demand")
```

**方式 4：先加载数据（灵活检查）**

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 先加载数据并检查
data = dslighting.load_data(
    "/path/to/data/competitions/bike-sharing-demand",
    registry_dir="/path/to/registry/bike-sharing-demand"
)

# 检查数据
print(data.show())

# 确认无误后运行
agent = dslighting.Agent()
result = agent.run(data)
```

### 4. 查看结果

```python
print(f"Workspace: {result.workspace_path}")
print(f"Score: {result.score}")
```

---

## 📖 核心概念

### 数据系统

DSLighting 使用统一的数据管理系统：

- **LoadedData**：核心数据容器，封装数据集和任务配置
- **TaskDetection**：自动识别任务类型（kaggle, open_ended, datasci）
- **Registry**：管理任务配置和评分规则

**查看数据结构：**

```python
data = dslighting.load_data(...)
print(data.show())
```

输出包括：
- 任务 ID 和类型
- 数据目录结构
- CSV 文件信息
- 任务描述和评估指标

### Agent 配置

```python
# 使用默认配置
agent = dslighting.Agent()

# 等价于：
agent = dslighting.Agent(
    workflow="aide",          # 工作流类型
    model="gpt-4o-mini",      # LLM 模型（从 .env 读取）
    temperature=0.7,          # 生成温度
    max_iterations=5          # 最大迭代次数
)
```

---

## 🔧 高级配置

### 自定义任务

创建自己的数据科学任务：

**目录结构：**

```
your-project/
├── data/competitions/
│   └── your-task-name/
│       └── prepared/
│           ├── public/      # train.csv, test.csv, sampleSubmission.csv
│           └── private/     # test_answer.csv
│
└── registry/
    └── your-task-name/
        ├── config.yaml      # 任务配置
        ├── description.md   # 任务描述
        └── grade.py         # 评分脚本（可选）
```

**config.yaml 示例：**

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
  name: rmsle  # 或 accuracy, f1, mae 等
```

**运行自定义任务：**

```python
result = agent.run(
    task_id="your-task-name",
    data_dir="/path/to/data/competitions",
    registry_dir="/path/to/registry"
)
```

### 常见问题

**Q: 为什么显示 "Score: N/A"？**

A: 这是 DSLighting 的已知问题。自动评分功能当前未启用，需要手动评分：

```python
from pathlib import Path
from mlebench.grade import grade_csv
from dsat.benchmark.mle import MLEBenchmarkRegistry

registry_dir = Path(dslighting.__file__).parent / "registry"
registry = MLEBenchmarkRegistry(registry_dir=str(registry_dir))
competition = registry.get_competition("bike-sharing-demand")

submission_files = list(result.workspace_path.glob("sandbox/submission_*.csv"))
if submission_files:
    report = grade_csv(submission_files[0], competition)
    print(f"✅ 实际 Score: {report.score}")
```

**Q: `load_dotenv()` 是必须的吗？**

A: 是的！必须在导入 `dslighting` 之前调用 `load_dotenv()` 来加载 `.env` 配置。

---

## 📚 完整文档

详细文档请访问：

- **[快速上手指南](https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html)** - 完整的安装、配置和使用教程
- **[数据系统文档](https://luckyfan-cs.github.io/dslighting-web/api/data-system.html)** - 深入了解数据管理和核心组件
- **[GitHub 项目](https://github.com/usail-hkust/dslighting)** - 源代码和问题反馈

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目基于 [AGPL-3.0 许可证](LICENSE) 发布。

---

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/usail-hkust/dslighting/issues)
- **文档**: [https://luckyfan-cs.github.io/dslighting-web/](https://luckyfan-cs.github.io/dslighting-web/)
- **PyPI**: [https://pypi.org/project/dslighting/](https://pypi.org/project/dslighting/)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️**

Made with ❤️ by [USAIL Lab](https://github.com/usail-hkust)

</div>
