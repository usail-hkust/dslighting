# DSLighting 安装选项速查表

## 快速安装

| 方式 | 命令 | 说明 |
|------|------|------|
| **标准安装** ⭐ | `pip install dslighting` | 包含所有功能（推荐） |
| **开发安装** | `pip install -e .[dev]` | 包含开发工具 |

## 包含的功能

标准安装（`pip install dslighting`）包含：

✅ **所有 6 种工作流**
- AIDE
- AutoKaggle
- Data Interpreter
- AutoMind
- DS-Agent
- DeepAnalyze

✅ **所有依赖**
- transformers (~300MB)
- torch (~200MB)
- Jupyter 生态 (~100MB)
- 其他核心包

**总大小：** ~650MB
**安装时间：** 5-10 分钟

## 网络受限环境

如果无法访问 HuggingFace：

```python
agent = dslighting.Agent(
    workflow="automind",  # 或 "dsagent"
    automind={             # 或 dsagent={}
        "enable_rag": False  # 禁用 HuggingFace 下载
    }
)
```

## 工作流速查

| 工作流 | 命令 | RAG 可选 |
|--------|------|----------|
| AIDE | `Agent(workflow="aide")` | ❌ |
| AutoKaggle | `Agent(workflow="autokaggle")` | ❌ |
| Data Interpreter | `Agent(workflow="data_interpreter")` | ❌ |
| AutoMind | `Agent(workflow="automind", automind={"enable_rag": False})` | ✅ |
| DS-Agent | `Agent(workflow="dsagent", dsagent={"enable_rag": False})` | ✅ |
| DeepAnalyze | `Agent(workflow="deepanalyze")` | ❌ |

## 快速验证

```python
import dslighting
print(dslighting.__version__)  # 查看版本
dslighting.help()              # 查看帮助
dslighting.list_workflows()    # 列出工作流
```
