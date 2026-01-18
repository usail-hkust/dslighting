# DSLighting v1.9.7 发布说明

## 🎉 新功能

### DS-Agent RAG 可选禁用

**问题描述**:
DS-Agent workflow 在使用 RAG（知识检索增强）功能时，同样需要从 HuggingFace 下载 embedding 模型，导致网络超时：

```
MaxRetryError("HTTPSConnectionPool(host='huggingface.co', port=443): Max retries exceeded...")
```

**解决方案**:
为 DS-Agent workflow 添加了 `enable_rag` 参数（与 AutoMind workflow 相同）：

```python
import dslighting

data = dslighting.load_data("bike-sharing-demand")

# 方法 1: 禁用 RAG（不需要 HuggingFace 连接）
agent = dslighting.Agent(
    workflow="dsagent",
    model="gpt-4o",
    dsagent={
        "enable_rag": False  # ✅ 不尝试下载 embedding 模型
    }
)

# 方法 2: 启用 RAG（默认行为）
agent = dslighting.Agent(
    workflow="dsagent",
    model="gpt-4o",
    dsagent={
        "enable_rag": True,  # 使用知识库（需要网络）
        "case_dir": "./experience_replay"
    }
)

result = agent.run(data)
```

**修改的文件**:
- `dsat/workflows/factory.py`:
  - `DSAgentWorkflowFactory.create_workflow()` 方法
  - 添加 `enable_rag` 参数读取（默认: `True`）
  - 当 `enable_rag=False` 时，将 `vdb_service` 设为 `None`

**技术细节**:

```python
# 修改前（强制启用 RAG）
case_dir = config.workflow.params.get('case_dir', 'experience_replay')
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

---

## ✅ 修复验证

### 测试: 禁用 RAG 模式

```python
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="dsagent",
    model="gpt-4o-mini",
    dsagent={
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

---

## 📦 安装

```bash
pip install --upgrade dslighting==1.9.7
```

---

## 🎯 影响范围

### 受影响的 Workflow
- ✅ **dsagent** - 新增 `enable_rag` 参数（可选禁用 RAG）
- ✅ **automind** - 已在 v1.9.6 添加相同功能
- ✅ **其他 workflows** - 无影响

### 参数变更

| Workflow | 参数 | 类型 | 默认值 | 说明 |
|----------|------|------|--------|------|
| dsagent | `enable_rag` | bool | `True` | 是否启用 RAG/知识库 |
| dsagent | `case_dir` | str | `"experience_replay"` | 知识库目录（仅在 `enable_rag=True` 时使用） |
| automind | `enable_rag` | bool | `True` | v1.9.6 已添加 |
| automind | `case_dir` | str | `"experience_replay"` | v1.9.6 已添加 |

---

## 📖 完整文档

- **PyPI**: https://pypi.org/project/dslighting/1.9.7/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/

---

## 🎉 总结

DSLighting v1.9.7 是一个 **功能增强版本**，为 DS-Agent workflow 添加了可选禁用 RAG 的能力（与 v1.9.6 的 AutoMind 功能一致）。

### 核心改进
- ✅ DS-Agent 新增 `enable_rag` 参数
- ✅ 支持在网络受限环境中运行 DS-Agent
- ✅ 保持 100% 向后兼容（默认行为不变）
- ✅ 更新文档和示例代码

### 推荐行动
- **DS-Agent workflow 用户**: 建议升级到 v1.9.7 以获得更好的网络容错能力
- **AutoMind workflow 用户**: 已在 v1.9.6 添加相同功能
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

### 与 AutoMind 对比

两个 workflow 现在都支持相同的 RAG 控制：

```python
# AutoMind (v1.9.6+)
agent = dslighting.Agent(
    workflow="automind",
    automind={"enable_rag": False}
)

# DS-Agent (v1.9.7+)
agent = dslighting.Agent(
    workflow="dsagent",
    dsagent={"enable_rag": False}
)
```

---

**版本**: DSLighting v1.9.7
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.9.6）
**类型**: 功能增强（DS-Agent RAG 可选禁用）
