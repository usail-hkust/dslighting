# DSLighting v1.9.0 发布说明

## 🎉 重大更新：嵌套字典参数格式

### 核心改进

DSLighting v1.9.0 引入了**全新的嵌套字典参数格式**，解决了 workflow 独有参数混淆的问题，提供了更清晰的 API 设计。

---

## ✨ 新特性

### 1️⃣ 嵌套字典参数格式（推荐）

**问题**：旧格式的参数名太长，容易混淆

```python
# ❌ 旧格式（v1.8.x）
agent = dslighting.Agent(
    workflow="autokaggle",
    autokaggle_max_attempts_per_phase=5,    # 太长！
    autokaggle_success_threshold=3.5         # 容易混淆！
)
```

**解决**：新的嵌套字典格式

```python
# ✅ 新格式（v1.9.0+，推荐）
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.5,

    # 清晰！参数独立，一目了然
    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)
```

### 2️⃣ 向后兼容

旧格式仍然支持，无需修改现有代码：

```python
# ✅ 仍然有效
agent = dslighting.Agent(
    workflow="autokaggle",
    autokaggle_max_attempts_per_phase=5,
    autokaggle_success_threshold=3.5
)
```

---

## 📋 所有 Workflow 的嵌套参数

### AIDE

```python
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    temperature=0.7,
    max_iterations=10,

    aide={
        "num_drafts": 5,
        "debug_prob": 0.8,
        "max_debug_depth": 10
    }
)
```

### AutoKaggle

```python
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.5,

    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)
```

### AutoMind

```python
agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",
    max_iterations=10,

    automind={
        "case_dir": "./experience_replay"
    }
)
```

### DS-Agent

```python
agent = dslighting.Agent(
    workflow="dsagent",
    model="gpt-4o",
    max_iterations=15,

    dsagent={
        "case_dir": "./experience_replay"
    }
)
```

### DataInterpreter & DeepAnalyze

```python
# DataInterpreter（无独有参数）
agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o",
    max_iterations=5
)

# DeepAnalyze（无独有参数）
agent = dslighting.Agent(
    workflow="deepanalyze",
    model="gpt-4o",
    max_iterations=10
)
```

---

## 🎯 参数对比

| 特性 | 嵌套字典（v1.9.0+） | 平铺格式（旧） |
|------|-------------------|--------------|
| **参数分类** | ✅ 清晰（workflow 独有参数独立） | ❌ 混淆（所有参数混在一起） |
| **可读性** | ✅ 高（一目了然） | ⚠️ 中（需要前缀区分） |
| **IDE 提示** | ✅ 完整 | ⚠️ 无提示 |
| **冲突风险** | ✅ 无 | ❌ 有（不同 workflow 可能冲突） |
| **向后兼容** | ✅ 支持 | ✅ 原生 |

---

## 📦 升级指南

### 如果你使用旧格式

**无需修改**！旧代码仍然完全兼容：

```python
# 旧代码（v1.8.x）仍然有效
agent = dslighting.Agent(
    workflow="autokaggle",
    autokaggle_max_attempts_per_phase=5,
    autokaggle_success_threshold=3.5
)
```

### 推荐迁移到新格式

新格式更清晰，推荐使用：

```python
# 新格式（v1.9.0+）
agent = dslighting.Agent(
    workflow="autokaggle",
    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)
```

---

## 🛠️ 技术细节

### 修改内容

1. **ConfigBuilder 增强**：
   - 支持 workflow 独有参数的嵌套字典格式
   - 自动识别并映射到正确的配置路径
   - 保留向后兼容性

2. **参数映射规则**：
   - `autokaggle` → `agent.autokaggle`
   - `aide` → `agent.search`
   - `automind`/`dsagent` → `workflow.params`

3. **优先级**：
   - 嵌套字典格式优先
   - 旧格式作为后备方案

---

## 📊 测试验证

所有测试通过：

```bash
================================================================================
测试 DSLighting v1.9.0 嵌套字典参数 API
================================================================================

✅ AutoKaggle 嵌套字典格式
✅ AIDE 嵌套字典格式
✅ AutoMind 嵌套字典格式
✅ DS-Agent 嵌套字典格式
✅ 旧格式向后兼容
✅ 完整配置示例

新 API 优势:
  ✅ 参数分类清晰
  ✅ 避免命名冲突
  ✅ 提高可读性
  ✅ 向后兼容
================================================================================
```

---

## 📚 文档更新

- ✅ **AGENT_PARAMETER_FLOW.md** - 完整参数传输链路（已更新）
- ✅ **WORKFLOW_QUICK_REFERENCE.md** - Workflow 快速参考（已更新）
- ✅ 所有示例代码使用新格式
- ✅ 保留旧格式示例以供参考

---

## 🚀 安装

```bash
pip install --upgrade dslighting==1.9.0
```

---

## 🔗 链接

- **PyPI**: https://pypi.org/project/dslighting/1.9.0/
- **完整文档**: https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html
- **GitHub**: https://github.com/usail-hkust/dslighting

---

## 🎉 总结

DSLighting v1.9.0 是一个**重要的 API 改进版本**，通过引入嵌套字典参数格式，解决了 workflow 独有参数混淆的问题，同时保持完全向后兼容。

### 核心特性
- ✅ 清晰的参数分类
- ✅ 避免 workflow 间参数冲突
- ✅ 提高代码可读性
- ✅ 完全向后兼容
- ✅ 更好的 IDE 支持

### 推荐行动
- **新用户**：直接使用新格式
- **现有用户**：可以选择性迁移，旧代码仍然有效
- **所有用户**：享受更清晰的 API 设计！

---

**版本**: DSLighting v1.9.0
**发布日期**: 2026-01-17
**向后兼容**: ✅ 是（100% 兼容 v1.8.x）
