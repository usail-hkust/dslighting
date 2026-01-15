# DSLighting Python API 快速上手指南

## 🚀 像使用 scikit-learn 一样简单

DSLighting 现在提供简化的 Python API，让您只需几行代码就能完成复杂的数据科学任务！

## ✨ 为什么选择 Python API？

| 特性 | 传统 DSAT API | DSLighting Python API |
|------|--------------|---------------------|
| **代码行数** | 15-20 行 | 1-3 行 |
| **学习曲线** | 需要理解多个概念 | 开箱即用 |
| **任务检测** | 手动配置 | 自动识别 |
| **异步处理** | 需要手动处理 | 自动处理 |
| **适用场景** | 复杂定制 | 快速原型 + 深度定制 |

## 📦 快速安装

```bash
# 1. 安装依赖
cd /path/to/dslighting
pip install -r requirements_local.txt

# 2. 安装 DSLighting 包
pip install -e .
```

## 🎯 三种使用方式

### 方式 1: 一行代码运行（最简单）

```python
import dslighting

# 自动检测任务类型并运行
result = dslighting.run_agent("data/competitions/titanic")

print(f"得分: {result.score}")
print(f"成本: ${result.cost:.4f}")
```

### 方式 2: 标准流程（推荐）

```python
import dslighting

# 1. 加载数据（自动检测任务类型）
data = dslighting.load_data("data/competitions/titanic")

# 2. 创建 Agent（使用默认配置）
agent = dslighting.Agent()

# 3. 运行
result = agent.run(data)

# 4. 查看结果
print(f"成功: {result.success}")
print(f"得分: {result.score}")
print(f"成本: ${result.cost:.4f}")
print(f"耗时: {result.duration:.1f}秒")
```

### 方式 3: 高级定制（完全控制）

```python
import dslighting

# 创建自定义 Agent
agent = dslighting.Agent(
    workflow="autokaggle",      # 工作流选择
    model="gpt-4o",            # 模型选择
    temperature=0.3,           # 温度参数
    max_iterations=10          # 最大迭代次数
)

# 运行任务
result = agent.run(
    "data/competitions/house-prices",
    output_path="my_submission.csv"  # 自定义输出路径
)
```

## 📊 支持的任务类型

DSLighting 会自动识别以下任务类型：

### 1. Kaggle 竞赛风格

```python
# 自动识别 train.csv, test.csv, sample_submission.csv
result = dslighting.run_agent("data/competitions/titanic")
```

**特征**：
- ✓ 目录包含 `train.csv` 和 `test.csv`
- ✓ 或包含 `prepared/public` 和 `prepared/private`
- ✓ 自动推荐：`autokaggle` 或 `aide` 工作流

### 2. 问答任务

```python
# 自动识别简短文本问题
result = dslighting.run_agent("什么是机器学习？")
print(f"答案: {result.output}")
```

**特征**：
- ✓ 输入是简短文本（<500 字符）
- ✓ 或字典格式
- ✓ 自动推荐：`aide` 工作流

### 3. DataFrame 输入

```python
import pandas as pd

df = pd.read_csv("my_data.csv")
result = dslighting.run_agent(df)
```

**特征**：
- ✓ 直接使用 pandas DataFrame
- ✓ 自动检测是否有目标列
- ✓ 自动推荐：`aide` 或 `data_interpreter` 工作流

### 4. 开放式探索

```python
# 目录包含 description.md 和 rubric.md
result = dslighting.run_agent("data/open-ended-task")
```

**特征**：
- ✓ 包含 `description.md` 和 `rubric.md`
- ✓ 自动推荐：`deepanalyze` 或 `automind` 工作流

## 🎨 工作流选择指南

| 工作流 | 适用场景 | 速度 | 成本 | 推荐指数 |
|--------|---------|------|------|----------|
| **aide** | 通用机器学习任务 | ⚡⚡⚡ | 💰💰 | ⭐⭐⭐⭐⭐ |
| **autokaggle** | Kaggle 竞赛 | ⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐ |
| **data_interpreter** | 快速数据分析 | ⚡⚡⚡⚡ | 💰 | ⭐⭐⭐⭐ |
| **automind** | 复杂推理任务 | ⚡⚡ | 💰💰💰 | ⭐⭐⭐ |
| **deepanalyze** | 深度数据探索 | ⚡ | 💰💰💰💰 | ⭐⭐⭐ |
| **dsagent** | 结构化任务 | ⚡⚡⚡ | 💰💰 | ⭐⭐⭐⭐ |

**自动推荐**：如果不指定，DSLighting 会根据任务类型自动推荐最合适的工作流。

## 💡 实用示例

### 示例 0: 快速开始 - bike-sharing-demand

```python
import dslighting

# 一行代码运行 bike-sharing-demand 预测
result = dslighting.run_agent("data/competitions/bike-sharing-demand")

print(f"得分: {result.score}")
print(f"成本: ${result.cost:.4f}")
```

**或者使用 AIDE 工作流**：

```python
import dslighting

# 创建 AIDE agent
agent = dslighting.Agent(workflow="aide")

# 运行 bike-sharing-demand
result = agent.run("data/competitions/bike-sharing-demand")

print(f"✓ 成功: {result.success}")
print(f"✓ 得分: {result.score}")
print(f"✓ 成本: ${result.cost:.4f}")
print(f"✓ 耗时: {result.duration:.1f}秒")
```

**完整示例**：查看 `examples/dslighting_api/example_bike_sharing.py`

### 示例 1: 批量处理多个任务

```python
import dslighting

agent = dslighting.Agent(workflow="aide")

# 批量运行
tasks = [
    "data/competitions/titanic",
    "data/competitions/house-prices",
    "data/competitions/fraud"
]

results = agent.run_batch(tasks)

# 查看所有结果
for i, result in enumerate(results):
    print(f"任务 {i+1}: 得分={result.score}, 成本=${result.cost:.4f}")
```

### 示例 2: 使用 DataFrame

```python
import dslighting
import pandas as pd

# 加载自己的数据
df = pd.read_csv("my_customer_data.csv")

# 运行预测
agent = dslighting.Agent()
result = agent.run(
    df,
    description="预测客户流失率",
    target_column="churn"  # 可选：指定目标列
)

# 保存结果
print(f"预测准确率: {result.score}")
```

### 示例 3: 自定义输出路径

```python
import dslighting

agent = dslighting.Agent()

result = agent.run(
    "data/competitions/titanic",
    output_path="my_submission.csv",
    task_id="my-experiment-001"
)

print(f"提交文件保存在: {result.output}")
```

### 示例 4: 访问底层组件

```python
import dslighting

agent = dslighting.Agent()

# 访问底层 DSATConfig（高级用法）
config = agent.get_config()
print(f"当前工作流: {config.workflow.name}")
print(f"当前模型: {config.llm.model}")

# 修改配置
config.llm.temperature = 0.5

# 访问 DSATRunner
runner = agent.get_runner()
```

## 🔧 环境配置

创建 `.env` 文件：

```bash
# 必需：LLM API 密钥
API_KEY=sk-your-api-key-here

# 可选：LLM 配置
LLM_MODEL=gpt-4o-mini
API_BASE=https://api.openai.com/v1

# 可选：DSLighting 配置
DSLIGHTING_DEFAULT_WORKFLOW=aide
DSLIGHTING_WORKSPACE_DIR=./runs/dslighting
```

## 📈 结果对象说明

`AgentResult` 包含以下信息：

```python
result = agent.run(data)

# 基本信息
result.success         # 是否成功
result.output          # 输出（预测、答案、文件路径等）
result.score           # 评估分数（如果有）

# 成本和性能
result.cost            # LLM 成本（美元）
result.duration        # 执行时间（秒）

# 文件路径
result.artifacts_path  # 生成产物的路径
result.workspace_path  # 工作空间路径

# 错误信息
result.error           # 错误消息（如果失败）

# 元数据
result.metadata        # 额外的元数据
```

## 🔄 从 DSAT API 迁移

### 之前（DSAT API）

```python
from dsat.config import DSATConfig, LLMConfig, WorkflowConfig
from dsat.runner import DSATRunner
from dsat.benchmark.mle import MLEBenchmark
import os
import asyncio

config = DSATConfig(
    llm=LLMConfig(
        model="gpt-4o-mini",
        api_key=os.getenv("API_KEY"),
        temperature=0.7
    ),
    workflow=WorkflowConfig(name="aide")
)

runner = DSATRunner(config)
benchmark = MLEBenchmark(
    name="mle",
    data_dir="data/competitions",
    log_path="runs/results"
)

eval_fn = runner.get_eval_function()
asyncio.run(benchmark.run_evaluation(eval_fn))
```

### 现在（Python API）

```python
import dslighting

result = dslighting.run_agent("data/competitions/titanic")
```

**代码量减少 90%+！**

## 📚 更多资源

- **API 详细文档**: [dslighting/README.md](../dslighting/README.md)
- **安装指南**: [INSTALLATION.md](../INSTALLATION.md)
- **基础示例**: [examples/dslighting_api/example_1_basic.py](../examples/dslighting_api/example_1_basic.py)
- **高级示例**: [examples/dslighting_api/example_2_advanced.py](../examples/dslighting_api/example_2_advanced.py)
- **迁移指南**: [examples/dslighting_api/example_3_migration.py](../examples/dslighting_api/example_3_migration.py)

## ❓ 常见问题

### Q: Python API 会替代 DSAT API 吗？

A: **不会！** 两者完全兼容：
- Python API 用于快速开发和原型
- DSAT API 用于深度定制
- 可以在同一项目中混用

### Q: 如何选择工作流？

A:
- **不知道选哪个** → 不指定，让系统自动推荐
- **Kaggle 竞赛** → 使用 `autokaggle`
- **快速分析** → 使用 `data_interpreter`
- **通用任务** → 使用 `aide`（默认）

### Q: 性能如何？

A:
- Python API 只是 DSAT API 的封装
- 底层完全相同，性能无差异
- 简化了接口，不牺牲功能

### Q: 如何处理大型数据集？

A:
```python
# 对于大型数据集，指定数据目录而不是加载整个 DataFrame
result = agent.run(
    "path/to/large/dataset",
    description="处理大型数据集"
)
```

## 🎉 开始使用

```bash
# 1. 安装
pip install -r requirements_local.txt
pip install -e .

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 运行第一个任务
python3 -c "
import dslighting
result = dslighting.run_agent('What is 9*8-2?')
print(f'答案: {result.output}')
"
```

**就这么简单！** 🚀

---

需要帮助？查看 [完整文档](../dslighting/README.md) 或在 [GitHub](https://github.com/usail-hkust/dslighting) 上提问。
