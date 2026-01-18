# DSLighting Quick Start Guide

5分钟快速上手 DSLighting 数据科学 Agent 框架。

---

## 📦 安装

```bash
pip install dslighting
```

或者指定版本：

```bash
pip install dslighting==1.9.0
```

---

## 🔑 设置 API Key

创建 `.env` 文件在你的项目目录：

```bash
# 创建 .env 文件
echo 'OPENAI_API_KEY=your_key_here' > .env
echo 'ANTHROPIC_API_KEY=your_key_here' >> .env
```

**重要**：不要将 `.env` 文件提交到 Git！

---

## 🚀 第一个 Agent（3 步开始）

### 步骤 1：加载环境变量

```python
from dotenv import load_dotenv
load_dotenv()
```

### 步骤 2：导入 DSLighting

```python
import dslighting
```

### 步骤 3：运行你的第一个 Agent

```python
# 使用内置数据集
result = dslighting.run_agent(
    task_id="bike-sharing-demand",
    workflow="aide"
)

print(f"Success! Score: {result.score}")
```

**完整代码**：

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

result = dslighting.run_agent(
    task_id="bike-sharing-demand",
    workflow="aide"
)

print(f"Score: {result.score}")
print(f"Cost: ${result.cost:.2f}")
print(f"Duration: {result.duration:.1f}s")
```

---

## 📊 使用你自己的数据

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 加载你的数据
data = dslighting.load_data("path/to/your/data.csv")

# 创建 Agent
agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini"
)

# 运行并添加自定义描述
result = agent.run(
    data,
    description="分析销售数据，找出趋势和异常点"
)

print(f"Output: {result.output}")
```

---

## 🎯 选择正确的 Workflow

### 快速参考表

| 任务类型 | 推荐 Workflow | 命令 |
|---------|--------------|------|
| 快速数据分析 | DataInterpreter | `workflow="data_interpreter"` |
| 简单竞赛 | AIDE | `workflow="aide"` |
| 复杂竞赛 | AutoKaggle | `workflow="autokaggle"` |
| 需要历史经验 | AutoMind | `workflow="automind"` |
| 长期任务 | DS-Agent | `workflow="dsagent"` |
| 深度分析 | DeepAnalyze | `workflow="deepanalyze"` |

### Workflow 详细说明

运行以下命令查看所有 workflow：

```bash
# CLI 命令
dslighting workflows

# 或 Python 命令
python -c "import dslighting; dslighting.list_workflows()"
```

---

## 💡 常用示例

### 示例 1：快速数据分析

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("sales_data.csv")

agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",
    max_iterations=5
)

result = agent.run(data, description="分析销售趋势")
print(f"Output: {result.output}")
```

### 示例 2：参加 Kaggle 竞赛

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.5,

    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)

result = agent.run(data)
print(f"Score: {result.score}")
```

### 示例 3：使用知识库（AutoMind）

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",

    automind={
        "case_dir": "./experience_replay"  # 经验回放目录
    }
)

result = agent.run(data)
print(f"Score: {result.score}")
```

---

## 🛠️ 获取帮助

### CLI 命令行帮助

```bash
# 查看主帮助
dslighting help

# 列出所有 workflow
dslighting workflows

# 查看 workflow 示例
dslighting example aide
dslighting example autokaggle

# 快速开始指南
dslighting quickstart

# 检测 Python 包
dslighting detect-packages

# 显示已检测的包
dslighting show-packages
```

### Python 交互式帮助

```python
import dslighting

# 显示帮助
dslighting.help()

# 列出所有 workflow
dslighting.list_workflows()

# 显示 workflow 示例
dslighting.show_example("aide")
dslighting.show_example("autokaggle")
```

---

## 📚 进阶用法

### 1. 自定义参数

```python
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",              # 模型选择
    temperature=0.5,             # 生成温度
    max_iterations=10,           # 最大迭代次数

    autokaggle={                 # AutoKaggle 独有参数
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)
```

### 2. 保留工作空间（调试用）

```python
agent = dslighting.Agent(
    workflow="aide",
    keep_workspace=True,         # 保留工作空间
    keep_workspace_on_failure=True  # 失败时也保留
)

result = agent.run(data)
# 工作空间不会被删除，可以查看中间结果
```

### 3. 使用不同的模型

```python
# 使用 OpenAI
agent = dslighting.Agent(model="gpt-4o")

# 使用 Anthropic
agent = dslighting.Agent(model="claude-3-5-sonnet-20241022")

# 使用 OpenRouter/第三方
agent = dslighting.Agent(model="openai/deepseek-ai/DeepSeek-V3")
```

### 4. 控制成本

```python
# 低成本快速测试
agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",        # 更便宜的模型
    max_iterations=3            # 减少迭代次数
)

# 高质量但昂贵
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    max_iterations=20,

    autokaggle={
        "max_attempts_per_phase": 10,
        "success_threshold": 4.5
    }
)
```

---

## ⚠️ 常见问题

### Q1: 如何查看 Agent 运行日志？

A: Agent 会自动显示运行日志。如果想保留工作空间查看详细日志：

```python
agent = dslighting.Agent(
    workflow="aide",
    keep_workspace=True  # 保留工作空间
)
```

### Q2: 如何选择 workflow？

A: 使用以下简单规则：

- **数据分析/探索** → `data_interpreter`
- **简单竞赛** → `aide`
- **复杂竞赛** → `autokaggle`
- **需要历史经验** → `automind`
- **长期任务** → `dsagent`
- **不确定** → `aide`（默认，最通用）

### Q3: 如何控制成本？

A: 三种方法：

1. **使用更便宜的模型**：`gpt-4o-mini` 而不是 `gpt-4o`
2. **减少迭代次数**：设置 `max_iterations=5`
3. **使用更简单的 workflow**：`data_interpreter` 而不是 `autokaggle`

### Q4: 结果如何评估？

A: 检查 `result` 对象：

```python
result = agent.run(data)

print(f"Score: {result.score}")           # 评分（如果有）
print(f"Output: {result.output}")         # 输出内容
print(f"Cost: ${result.cost:.2f}")        # 成本
print(f"Duration: {result.duration:.1f}s") # 运行时间
print(f"Success: {result.success}")       # 是否成功
```

### Q5: 如何使用内置数据集？

A: 直接使用 `task_id`：

```python
# 内置数据集列表：
# - bike-sharing-demand
# - house-prices
# - titanic
# - 以及更多...

result = dslighting.run_agent(task_id="bike-sharing-demand")
```

---

## 📖 下一步

1. **查看所有 workflow**：
   ```bash
   dslighting workflows
   ```

2. **查看 workflow 示例**：
   ```bash
   dslighting example autokaggle
   ```

3. **阅读完整文档**：
   - https://luckyfan-cs.github.io/dslighting-web/

4. **查看 GitHub**：
   - https://github.com/usail-hkust/dslighting

---

## 🎓 总结

DSLighting 让数据科学变得简单：

✅ **3 行代码**开始使用
✅ **6 种 workflow** 覆盖所有场景
✅ **自动调优** 无需手动调参
✅ **内置评分** 自动评估结果
✅ **完整文档** 和帮助系统

**现在就开始**：

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

result = dslighting.run_agent(
    task_id="bike-sharing-demand",
    workflow="aide"
)

print(f"Success! Score: {result.score}")
```

**版本**: DSLighting v1.9.0+
**更新**: 2026-01-17

---

## 💬 获取支持

- 📧 提交 Issue: https://github.com/usail-hkust/dslighting/issues
- 📖 文档: https://luckyfan-cs.github.io/dslighting-web/
- 💬 讨论: https://github.com/usail-hkust/dslighting/discussions
