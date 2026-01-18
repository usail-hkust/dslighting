# DSLighting v1.9.6 发布说明

## 🎉 新功能

### AutoMind RAG 可选禁用

**问题描述**:
AutoMind workflow 在使用 RAG（知识检索增强）功能时，需要从 HuggingFace 下载 embedding 模型，这在网络受限或测试环境中可能导致超时错误：

```
MaxRetryError("HTTPSConnectionPool(host='huggingface.co', port=443): Max retries exceeded with url: /BAAI/llm-embedder/...")
Connection to huggingface.co timed out. (connect timeout=10)
```

**解决方案**:
为 AutoMind workflow 添加了 `enable_rag` 参数，允许用户禁用 RAG 功能：

```python
import dslighting

data = dslighting.load_data("bike-sharing-demand")

# 方法 1: 禁用 RAG（不需要 HuggingFace 连接）
agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",
    automind={
        "enable_rag": False  # ✅ 不尝试下载 embedding 模型
    }
)

# 方法 2: 启用 RAG（默认行为）
agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",
    automind={
        "enable_rag": True,  # 使用知识库（需要网络）
        "case_dir": "./experience_replay"
    }
)

result = agent.run(data)
```

**适用场景**:
| 场景 | 推荐设置 | 说明 |
|------|----------|------|
| **网络受限** | `enable_rag=False` | 避免超时错误 |
| **快速测试** | `enable_rag=False` | 跳过知识库加载，加快启动 |
| **无历史经验** | `enable_rag=False` | 首次运行，没有经验数据 |
| **生产环境** | `enable_rag=True` | 使用知识库提升性能 |

**修改的文件**:
- `dsat/workflows/factory.py`:
  - `AutoMindWorkflowFactory.create_workflow()` 方法
  - 添加 `enable_rag` 参数读取（默认: `True`）
  - 当 `enable_rag=False` 时，将 `vdb_service` 设为 `None`

**技术细节**:

```python
# 修改前（强制启用 RAG）
vdb_service = VDBService(case_dir=case_dir)  # ❌ 总是尝试连接 HuggingFace

# 修改后（可选 RAG）
enable_rag = config.workflow.params.get('enable_rag', True)
vdb_service = None
if enable_rag:
    case_dir = config.workflow.params.get('case_dir', 'experience_replay')
    vdb_service = VDBService(case_dir=case_dir)
    logger.info(f"RAG enabled: Using knowledge base from {case_dir}")
else:
    logger.info("RAG disabled: Running without knowledge base retrieval")
```

**向后兼容性**:
- ✅ 完全向后兼容：默认 `enable_rag=True` 保持原有行为
- ✅ AutoMind workflow 已经有处理 `vdb_service=None` 的逻辑：
  ```python
  if self.vdb_service:  # 自动检查 RAG 是否启用
      cases = self.vdb_service.retrieve(task_goal, top_k=2)
  ```

---

## ✅ 修复验证

### 测试 1: 禁用 RAG 模式

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o-mini",
    automind={
        "enable_rag": False  # 关闭 RAG
    }
)

result = agent.run(data)

# 预期结果：
# - ✅ 不会尝试连接 huggingface.co
# - ✅ 不会下载 embedding 模型
# - ✅ Workflow 正常运行（只是不使用知识库）
# - ✅ 日志显示 "RAG disabled: Running without knowledge base retrieval"
```

### 测试 2: 启用 RAG 模式（默认）

```python
agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",
    automind={
        "enable_rag": True,  # 或省略（默认 True）
        "case_dir": "./experience_replay"
    }
)

# 预期结果：
# - ✅ 正常连接 HuggingFace
# - ✅ 下载并使用 embedding 模型
# - ✅ 从 experience_replay 目录检索知识
# - ✅ 日志显示 "RAG enabled: Using knowledge base from ./experience_replay"
```

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.9.6
```

---

## 🎯 影响范围

### 受影响的 Workflow
- ✅ **automind** - 新增 `enable_rag` 参数（可选禁用 RAG）
- ✅ **其他 workflows** - 无影响

### 参数变更

| Workflow | 参数 | 类型 | 默认值 | 说明 |
|----------|------|------|--------|------|
| automind | `enable_rag` | bool | `True` | 是否启用 RAG/知识库 |
| automind | `case_dir` | str | `"experience_replay"` | 知识库目录（仅在 `enable_rag=True` 时使用） |

---

## 📖 完整文档

- **PyPI**: https://pypi.org/project/dslighting/1.9.6/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/

---

## 🎉 总结

DSLighting v1.9.6 是一个 **功能增强版本**，为 AutoMind workflow 添加了可选禁用 RAG 的能力。

### 核心改进
- ✅ 新增 `enable_rag` 参数用于 AutoMind workflow
- ✅ 支持在网络受限环境中运行 AutoMind
- ✅ 保持 100% 向后兼容（默认行为不变）
- ✅ 更新文档和示例代码

### 推荐行动
- **AutoMind workflow 用户**: 建议升级到 v1.9.6 以获得更好的网络容错能力
- **所有用户**: 可选升级（不影响其他 workflows）

### 使用建议

**何时禁用 RAG** (`enable_rag=False`):
- 网络无法访问 HuggingFace
- 快速测试或原型开发
- 没有历史经验数据
- 希望减少启动时间

**何时启用 RAG** (`enable_rag=True`, 默认):
- 有稳定的网络连接
- 已积累经验数据（experience_replay/）
- 生产环境运行
- 需要最佳性能

---

**版本**: DSLighting v1.9.6
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.9.5）
**类型**: 功能增强（可选 RAG 禁用）
