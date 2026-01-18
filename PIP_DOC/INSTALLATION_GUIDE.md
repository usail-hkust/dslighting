# DSLighting 安装指南

**版本：** v1.9.8+
**更新时间：** 2026-01-18

---

## 📦 安装方式

### 标准安装（推荐）⭐

```bash
pip install dslighting
```

**包含内容：**
- ✅ 所有 6 种工作流（AIDE、AutoKaggle、Data Interpreter、AutoMind、DS-Agent、DeepAnalyze）
- ✅ RAG 支持（transformers + torch）
- ✅ Jupyter 支持（Data Interpreter）
- ✅ 所有功能完整可用

**包大小：** ~650MB
**安装时间：** 5-10 分钟

---

### 开发安装

**适用于：** 贡献者和开发者

```bash
# 克隆仓库
git clone https://github.com/usail-hkust/dslighting.git
cd dslighting

# 开发安装（包含开发工具）
pip install -e .[dev]
```

**额外包含：**
- 测试框架（pytest）
- 代码检查工具（black, mypy, ruff）
- 构建工具（build, twine）

---

## 🚀 快速验证

安装完成后，验证安装是否成功：

```python
import dslighting

# 查看版本
print(dslighting.__version__)

# 查看帮助
dslighting.help()

# 列出所有工作流
dslighting.list_workflows()
```

---

## 📋 所有工作流

安装后即可使用所有工作流，无需额外安装：

| 工作流 | 描述 | 使用场景 |
|--------|------|----------|
| **AIDE** | Adaptive Iteration & Debugging | Kaggle 竞赛、数据分析 |
| **AutoKaggle** | 高级竞赛求解器 | 复杂 Kaggle 竞赛 |
| **Data Interpreter** | 交互式数据分析 | 数据探索、可视化 |
| **AutoMind** | 知识库增强规划 | 复杂任务、历史经验 |
| **DS-Agent** | 长期规划与日志 | 长期任务、详细记录 |
| **DeepAnalyze** | 深度结构化分析 | 深度分析、推理任务 |

---

## 💡 使用示例

### 基本工作流

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

# 方法1: 使用内置数据集
data = dslighting.load_data("bike-sharing-demand")

# 方法2: 使用自定义数据
data = dslighting.load_data("./my_data.csv")

# 运行 AIDE 工作流
agent = dslighting.Agent(workflow="aide")
result = agent.run(data)

print(f"Score: {result.score}")
print(f"Cost: ${result.cost:.2f}")
```

### AutoMind（带 RAG）

```python
# 启用 RAG（使用知识库）
agent = dslighting.Agent(
    workflow="automind",
    automind={
        "enable_rag": True,
        "case_dir": "./experience_replay"
    }
)

# 禁用 RAG（不从 HuggingFace 下载 embedding）
agent = dslighting.Agent(
    workflow="automind",
    automind={
        "enable_rag": False
    }
)
```

### DS-Agent（带 RAG）

```python
# 启用 RAG
agent = dslighting.Agent(
    workflow="dsagent",
    dsagent={
        "enable_rag": True,
        "case_dir": "./experience_replay"
    }
)

# 禁用 RAG
agent = dslighting.Agent(
    workflow="dsagent",
    dsagent={
        "enable_rag": False
    }
)
```

### Data Interpreter

```python
# Data Interpreter 需要 Jupyter 支持（已包含）
agent = dslighting.Agent(workflow="data_interpreter")
result = agent.run(data, description="分析销售趋势")
```

---

## 🔧 关于 enable_rag 参数

**重要说明：**

`enable_rag` 参数控制**是否使用知识库检索功能**，但**不影响安装**。

- ✅ `enable_rag=True`（默认）：使用知识库，从 experience_replay 目录学习
- ✅ `enable_rag=False`：不使用知识库，但 transformers 和 torch 仍然已安装

**为什么？**

VDBService（向量数据库服务）在代码级别依赖 transformers 和 torch，所以这些包是必需的。`enable_rag=False` 只是跳过 VDBService 的初始化，避免从 HuggingFace 下载 embedding 模型。

---

## 🌐 网络受限环境

如果你在网络受限的环境中（无法访问 HuggingFace）：

```python
# 禁用 RAG 功能
agent = dslighting.Agent(
    workflow="automind",  # 或 "dsagent"
    automind={             # 或 dsagent={}
        "enable_rag": False  # 关键：禁用 HuggingFace 下载
    }
)
```

这样就不会尝试从 HuggingFace 下载 embedding 模型，但依然可以使用 AutoMind/DS-Agent 的其他功能。

---

## 📊 依赖说明

### 核心依赖（~650MB）

| 包名 | 大小 | 用途 |
|------|------|------|
| pandas | ~50MB | 数据处理 |
| transformers | ~300MB | NLP 模型（RAG） |
| torch | ~200MB | 深度学习框架 |
| scikit-learn | ~50MB | 机器学习 |
| Jupyter 生态 | ~100MB | Data Interpreter |
| 其他 | ~50MB | LLM、配置等 |

### 为什么 transformers 和 torch 是必需的？

即使不使用 RAG 功能，代码中的 `VDBService` 类仍然会导入这些包。这是由当前代码架构决定的。

---

## 🔧 常见问题

### Q1: 为什么安装时间这么长？

**A:** DSLighting 包含 transformers (~300MB) 和 torch (~200MB)，这些是大型机器学习库，下载和安装需要 5-10 分钟。

---

### Q2: 可以只安装部分功能吗？

**A:** 目前不行。所有工作流都需要完整的依赖包。`enable_rag=False` 只是运行时配置，不影响安装。

---

### Q3: 如何避免 HuggingFace 下载？

**A:** 使用 `enable_rag=False` 参数：

```python
agent = dslighting.Agent(
    workflow="automind",
    automind={"enable_rag": False}
)
```

---

### Q4: 离线环境如何安装？

**A:**

```bash
# 在有网络的机器上下载
pip download dslighting -d ./packages

# 在离线机器上安装
pip install --no-index --find-links=./packages dslighting
```

---

### Q5: 如何检查安装是否成功？

**A:**

```bash
# 检查版本
python -c "import dslighting; print(dslighting.__version__)"

# 运行帮助命令
dslighting help

# 列出工作流
dslighting workflows
```

---

## 🆘 获取帮助

如果遇到安装问题：

1. **检查 Python 版本**：需要 Python 3.10+
   ```bash
   python --version
   ```

2. **检查 pip 版本**：建议升级 pip
   ```bash
   pip install --upgrade pip
   ```

3. **查看详细错误**：
   ```bash
   pip install dslighting -v
   ```

4. **提交 Issue**：
   https://github.com/usail-hkust/dslighting/issues

---

## 📚 相关文档

- [快速开始指南](QUICK_START.md)
- [工作流参考](WORKFLOW_QUICK_REFERENCE.md)
- [参数配置](AGENT_UNIQUE_PARAMETERS.md)
- [发布说明](RELEASE_NOTES_v1.9.7.md)

---

**最后更新：** 2026-01-18
**文档版本：** 2.0
