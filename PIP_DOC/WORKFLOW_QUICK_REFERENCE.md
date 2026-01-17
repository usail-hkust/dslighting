# DSLighting Workflow 快速参考 (v1.9.0+)

本文档提供所有 6 种 workflow 的快速参考指南。

**v1.9.0 新特性**：嵌套字典参数格式，参数分类更清晰！

---

## 🚀 快速选择指南

| 任务类型 | 推荐 Workflow | 命令 |
|---------|--------------|------|
| Kaggle 竞赛（简单） | AIDE | `Agent(workflow="aide")` |
| Kaggle 竞赛（复杂） | AutoKaggle | `Agent(workflow="autokaggle")` |
| 数据探索 | DataInterpreter | `Agent(workflow="data_interpreter")` |
| 深度分析 | DeepAnalyze | `Agent(workflow="deepanalyze")` |
| 复杂规划 | AutoMind | `Agent(workflow="automind")` |
| 长期任务 | DS-Agent | `Agent(workflow="dsagent")` |

---

## 📋 Workflow 速查表（v1.9.0+ 新 API）

### 1. AIDE（默认）

```python
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    temperature=0.7,
    max_iterations=10,

    # AIDE 独有参数（嵌套字典）
    aide={
        "num_drafts": 5,
        "debug_prob": 0.8,
        "max_debug_depth": 10
    }
)
```

---

### 2. AutoKaggle（推荐用于竞赛）

```python
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.5,

    # AutoKaggle 独有参数（嵌套字典）
    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)
```

---

### 3. DataInterpreter

```python
agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",
    temperature=0.7,
    max_iterations=5
    # DataInterpreter 无独有参数
)
```

---

### 4. AutoMind

```python
agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",
    temperature=0.5,
    max_iterations=10,

    # AutoMind 独有参数（嵌套字典）
    automind={
        "case_dir": "./experience_replay"
    }
)
```

---

### 5. DS-Agent

```python
agent = dslighting.Agent(
    workflow="dsagent",
    model="gpt-4o",
    temperature=0.6,
    max_iterations=15,

    # DS-Agent 独有参数（嵌套字典）
    dsagent={
        "case_dir": "./experience_replay"
    }
)
```

---

### 6. DeepAnalyze

```python
agent = dslighting.Agent(
    workflow="deepanalyze",
    model="gpt-4o",
    temperature=0.8,
    max_iterations=10
    # DeepAnalyze 无独有参数
)
```

---

## 🆚 新旧 API 对比

### 旧格式（v1.8.x）

```python
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    autokaggle_max_attempts_per_phase=5,    # ❌ 太长，易混淆
    autokaggle_success_threshold=3.5         # ❌ 不清晰属于哪个 workflow
)
```

### 新格式（v1.9.0+，推荐）

```python
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",

    # ✅ 清晰！参数独立，一目了然
    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)
```

---

## 🎯 常用配置模板（v1.9.0+）

### 模板1：高质量竞赛（最贵但最好）

```python
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.3,
    autokaggle={
        "max_attempts_per_phase": 10,
        "success_threshold": 4.5
    }
)
# 预期成本: $5-20
# 预期时间: 30-60分钟
# 适用: 重要竞赛，追求最高质量
```

### 模板2：平衡性能（推荐）

```python
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    temperature=0.5,
    max_iterations=10,
    aide={
        "num_drafts": 5,
        "debug_prob": 0.8,
        "max_debug_depth": 10
    }
)
# 预期成本: $2-10
# 预期时间: 15-30分钟
# 适用: 大多数竞赛任务
```

### 模板3：快速原型

```python
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o-mini",
    temperature=0.7,
    max_iterations=5,
    aide={
        "num_drafts": 3,
        "debug_prob": 0.7
    }
)
# 预期成本: $0.5-2
# 预期时间: 5-10分钟
# 适用: 快速验证想法
```

### 模板4：低成本探索

```python
agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",
    max_iterations=3,
    temperature=0.7
)
# 预期成本: $0.1-0.5
# 预期时间: 2-5分钟
# 适用: 数据快速查看
```

### 模板5：极限性能（不惜成本）

```python
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.2,
    autokaggle={
        "max_attempts_per_phase": 15,
        "success_threshold": 5.0
    }
)
# 预期成本: $10-50
# 预期时间: 60-120分钟
# 适用: 决赛、重要项目
```

---

## 📊 Workflow 选择决策树

```
开始
  ↓
是 Kaggle 竞赛吗？
  ├─ 是 → 任务复杂吗？
  │       ├─ 简单 → AIDE
  │       └─ 复杂 → AutoKaggle
  │
  └─ 否 → 需要深度分析吗？
          ├─ 是 → DeepAnalyze
          └─ 否 → 需要多轮对话吗？
                  ├─ 是 → DataInterpreter
                  └─ 否 → 需要复杂规划吗？
                          ├─ 是 → AutoMind
                          └─ 否 → DS-Agent
```

---

## 🔧 参数调优建议

### max_iterations（迭代次数）

| Workflow | 保守 | 标准 | 激进 |
|----------|------|------|------|
| AIDE | 5 | 10 | 15 |
| AutoKaggle | 8 | 12 | 20 |
| DataInterpreter | 3 | 5 | 8 |
| AutoMind | 5 | 10 | 15 |
| DS-Agent | 10 | 15 | 25 |
| DeepAnalyze | 5 | 10 | 15 |

### temperature（温度）

| 场景 | 温度范围 | 说明 |
|------|---------|------|
| 精确任务 | 0.2-0.4 | 输出确定性强 |
| 平衡 | 0.5-0.7 | 兼顾创造性和准确性 |
| 探索性 | 0.8-1.0 | 高创造性，可能不稳定 |

### num_drafts（草稿数）- 仅 AIDE

| 场景 | 草稿数 | 说明 |
|------|--------|------|
| 快速 | 2-3 | 速度快，多样性低 |
| 平衡 | 5-7 | 推荐配置 |
| 深度 | 8-10 | 多样性高，成本高 |

---

## ⚡ 性能对比

| Workflow | 速度 | 质量 | 成本 | 复杂度 |
|----------|------|------|------|--------|
| AIDE | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| AutoKaggle | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| DataInterpreter | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ |
| AutoMind | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| DS-Agent | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| DeepAnalyze | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

---

## 📝 完整示例

### 示例1：参加 Kaggle 竞赛

```python
import dslighting

# 设置
dslighting.setup(
    data_parent_dir="/path/to/competitions",
    registry_parent_dir="/path/to/registry"
)

# 创建 agent
agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.5,
    max_iterations=10,
    autokaggle_max_attempts_per_phase=5
)

# 运行
result = agent.run(task_id="bike-sharing-demand")

# 查看结果
print(f"Score: {result.score}")
print(f"Cost: ${result.cost:.2f}")
print(f"Duration: {result.duration:.1f}s")
```

### 示例2：数据分析

```python
import dslighting

# 创建 agent
agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o",
    max_iterations=8
)

# 运行
result = agent.run(
    data="sales_data.csv",
    description="分析销售趋势，找出异常点和增长机会"
)

# 查看结果
print(f"Analysis: {result.output}")
```

### 示例3：快速原型

```python
import dslighting

# 一行代码运行
result = dslighting.run_agent(
    task_id="bike-sharing-demand",
    workflow="aide",
    max_iterations=5,
    model="gpt-4o-mini"
)
```

---

## 📚 更多资源

- **完整参数文档**: [AGENT_PARAMETER_FLOW.md](./AGENT_PARAMETER_FLOW.md)
- **快速上手**: [QUICK_GUIDE.md](./QUICK_GUIDE.md)
- **API指南**: [API_GUIDE.md](./API_GUIDE.md)
- **在线文档**: https://luckyfan-cs.github.io/dslighting-web/

---

**版本**: DSLighting v1.8.3
**更新时间**: 2026-01-17
