# DSLighting Python API 示例

本目录包含 DSLighting Python API 的使用示例。

## 📁 示例文件

### 基础示例

#### 1. example_1_basic.py
**基础用法示例** - 最简单的使用方式

```bash
python examples/dslighting_api/example_1_basic.py
```

**内容**：
- 一行代码运行
- 标准三步流程
- 问答任务示例

**适合**：第一次接触 DSLighting 的用户

---

#### 2. example_2_advanced.py
**高级用法示例** - 深度定制

```bash
python examples/dslighting_api/example_2_advanced.py
```

**内容**：
- 自定义工作流和模型
- 批量处理
- 访问底层组件
- DataFrame 输入
- 自定义输出路径

**适合**：需要更多控制的用户

---

#### 3. example_3_migration.py
**迁移指南** - 从 DSAT API 迁移

```bash
python examples/dslighting_api/example_3_migration.py
```

**内容**：
- DSAT API vs DSLighting API 对比
- 三种迁移路径
- 渐进式迁移策略

**适合**：现有 DSAT 用户

---

### 实战示例

#### 4. example_bike_sharing.py ⭐ 推荐
**Bike Sharing Demand 完整示例**

```bash
python examples/dslighting_api/example_bike_sharing.py
```

**内容**：
- 使用真实的 Kaggle 数据集
- AIDE 工作流演示
- 5 种不同的使用模式
- 详细的代码解释

**特点**：
- ✅ 使用真实数据（bike-sharing-demand）
- ✅ 完整的代码示例
- ✅ 清晰的注释说明
- ✅ 多种配置选项

**适合**：所有用户，推荐从这里开始！

---

#### 5. run_bike_sharing.py ⭐⭐ 快速开始
**可运行的 Bike Sharing 脚本**

```bash
python examples/dslighting_api/run_bike_sharing.py
```

**内容**：
- 完整的可执行代码
- 步骤化执行流程
- 详细的结果输出
- 即拷即用

**特点**：
- ✅ 取消注释即可运行
- ✅ 完整的执行流程
- ✅ 详细的结果展示
- ✅ 适合新手

**适合**：想要快速看到效果的用户

---

## 🚀 快速开始

### 方式 1: 查看示例（推荐新手）

```bash
# 1. 查看基础示例
cat examples/dslighting_api/example_1_basic.py

# 2. 查看实战示例
cat examples/dslighting_api/example_bike_sharing.py

# 3. 运行可执行脚本
python examples/dslighting_api/run_bike_sharing.py
```

### 方式 2: 自己尝试

```python
import dslighting

# 使用 bike-sharing-demand 数据集
result = dslighting.run_agent("data/competitions/bike-sharing-demand")

print(f"得分: {result.score}")
print(f"成本: ${result.cost:.4f}")
```

---

## 📊 示例对比

| 示例 | 难度 | 可运行 | 数据集 | 推荐度 |
|------|------|--------|--------|--------|
| example_1_basic.py | ⭐ | ❌ | 无 | ⭐⭐⭐ |
| example_2_advanced.py | ⭐⭐⭐ | ❌ | 无 | ⭐⭐⭐⭐ |
| example_3_migration.py | ⭐⭐ | ❌ | 无 | ⭐⭐⭐⭐ |
| example_bike_sharing.py | ⭐⭐ | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| run_bike_sharing.py | ⭐ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |

---

## 💡 推荐学习路径

### 新手路径

1. **阅读** `example_1_basic.py` - 了解基本概念
2. **阅读** `example_bike_sharing.py` - 看真实示例
3. **运行** `run_bike_sharing.py` - 亲手试一试
4. **修改** `run_bike_sharing.py` - 尝试不同参数

### 进阶路径

1. **阅读** `example_2_advanced.py` - 了解高级功能
2. **阅读** `example_3_migration.py` - 如果之前用过 DSAT
3. **尝试** 不同工作流和参数
4. **访问** 底层组件进行深度定制

---

## 🔧 运行前准备

### 1. 安装依赖

```bash
pip install -r requirements_local.txt
pip install -e .
```

### 2. 配置 API 密钥

```bash
cp .env.example .env
# 编辑 .env 文件，设置 API_KEY
```

### 3. 准备数据（可选）

```bash
# bike-sharing-demand 数据已包含
ls data/competitions/bike-sharing-demand/
```

---

## 📝 代码示例

### 最简单的例子

```python
import dslighting

# 一行代码
result = dslighting.run_agent("data/competitions/bike-sharing-demand")
```

### 使用 AIDE 工作流

```python
import dslighting

# 创建 agent
agent = dslighting.Agent(workflow="aide")

# 运行
result = agent.run("data/competitions/bike-sharing-demand")

# 查看结果
print(f"得分: {result.score}")
```

### 自定义配置

```python
import dslighting

# 自定义 agent
agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o-mini",
    temperature=0.7,
    max_iterations=5
)

# 运行
result = agent.run("data/competitions/bike-sharing-demand")
```

---

## 🎯 常见任务

### 不同的数据集

```python
# Kaggle 竞赛
result = dslighting.run_agent("data/competitions/titanic")
result = dslighting.run_agent("data/competitions/bike-sharing-demand")
result = dslighting.run_agent("data/competitions/house-prices")

# 问答任务
result = dslighting.run_agent("What is 9*8-2?")

# DataFrame
import pandas as pd
df = pd.read_csv("my_data.csv")
result = dslighting.run_agent(df)
```

### 不同的工作流

```python
# AIDE - 通用机器学习
agent = dslighting.Agent(workflow="aide")

# AutoKaggle - Kaggle 竞赛优化
agent = dslighting.Agent(workflow="autokaggle")

# DataInterpreter - 快速数据分析
agent = dslighting.Agent(workflow="data_interpreter")
```

---

## 📚 更多资源

- **Python API 快速上手**: [docs/python-api-guide.md](../../docs/python-api-guide.md)
- **API 完整文档**: [dslighting/README.md](../../dslighting/README.md)
- **安装指南**: [INSTALLATION.md](../../INSTALLATION.md)
- **主文档**: https://luckyfan-cs.github.io/dslighting-web/

---

## ❓ 获取帮助

如果遇到问题：

1. 查看示例代码的注释
2. 阅读 [Python API 快速上手指南](../../docs/python-api-guide.md)
3. 查看 [常见问题](../../docs/python-api-guide.md#-常见问题)
4. 在 [GitHub](https://github.com/usail-hkust/dslighting) 提问
