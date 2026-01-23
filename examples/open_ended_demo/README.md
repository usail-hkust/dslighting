# DSLighting Quick Start Tutorial

这是一个简单易懂的 DSLighting 教程，展示如何使用三个开放式 API 进行数据处理、分析和建模。

## 📋 目录

- [环境准备](#环境准备)
- [安装 DSLighting](#安装-dslighting)
- [配置环境变量](#配置环境变量)
- [使用示例](#使用示例)
- [三个 API 详解](#三个-api-详解)

---

## 🚀 环境准备

### 1. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv dslighting-env

# 激活虚拟环境
# macOS/Linux:
source dslighting-env/bin/activate

# Windows:
# dslighting-env\Scripts\activate
```

### 2. 升级 pip

```bash
pip install --upgrade pip
```

---

## 📦 安装 DSLighting

### 方式 1: 基础安装（推荐）

```bash
pip install dslighting
```

### 方式 2: 完整安装（包含可视化）

```bash
pip install dslighting matplotlib seaborn
```

### 验证安装

```bash
python -c "import dslighting; print(f'DSLighting {dslighting.__version__} installed!')"
```

---

## ⚙️ 配置环境变量

### 1. 创建 `.env` 文件

在项目目录下创建 `.env` 文件：

```bash
cd /path/to/your/project
touch .env
```

### 2. 编辑 `.env` 文件

添加以下内容（根据你的 LLM 提供商配置）：

```bash
# OpenAI 配置
API_KEY=sk-your-openai-api-key-here
API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# 或者使用其他兼容 OpenAI 的 API
# API_KEY=your-api-key
# API_BASE=https://api.deepseek.com/v1
# LLM_MODEL=deepseek-chat
```

### 3. 获取 API Key

- **OpenAI**: https://platform.openai.com/api-keys
- **DeepSeek**: https://platform.deepseek.com/
- **其他提供商**: 查看 LLM 提供商的文档

---

## 🎯 使用示例

### 快速开始

```python
import dslighting

# 1. 数据分析
result = dslighting.analyze(
    data="path/to/your/data.csv",
    description="分析数据的基本统计特征和分布",
    model="gpt-4o"  # 或您的模型名称
)

# 2. 数据处理
result = dslighting.process(
    data="path/to/your/data.csv",
    description="清洗数据，处理缺失值和异常值",
    model="gpt-4o"  # 或您的模型名称
)

# 3. 数据建模
result = dslighting.model(
    data="path/to/your/data.csv",
    description="训练机器学习模型并进行预测",
    model="gpt-4o"  # 或您的模型名称
)
```

---

## 📚 三个 API 详解

### 1️⃣ `analyze()` - 数据分析

**用途**: 探索性数据分析（EDA）

**特点**:
- 默认迭代次数: 2
- 适合快速了解数据
- 生成统计摘要和可视化
- 自动保留工作空间

**示例**:

```python
import dslighting

result = dslighting.analyze(
    data="data/titanic.csv",
    description="分析泰坦尼克号乘客数据的特征分布",
    model="gpt-4o"  # 指定模型
)

# 查看结果
print(result.summary)
print(result.artifacts)
```

**适用场景**:
- 数据初步探索
- 特征分布分析
- 相关性分析
- 异常值检测

---

### 2️⃣ `process()` - 数据处理

**用途**: 数据清洗和预处理

**特点**:
- 默认迭代次数: 3
- 自动检测和处理问题
- 保持数据质量
- 自动保留工作空间

**示例**:

```python
import dslighting

result = dslighting.process(
    data="data/messy_data.csv",
    description="清洗数据：填充缺失值、删除重复行、处理异常值",
    model="gpt-4o"  # 指定模型
)

# 查看处理后的数据
print(result.summary)
```

**适用场景**:
- 数据清洗
- 特征工程
- 数据转换
- 缺失值处理

---

### 3️⃣ `model()` - 数据建模

**用途**: 机器学习建模和预测

**特点**:
- 默认迭代次数: 4
- 自动选择模型
- 模型评估和优化
- 自动保留工作空间

**示例**:

```python
import dslighting

result = dslighting.model(
    data="data/training.csv",
    description="训练分类模型预测乘客生存",
    model="gpt-4o"  # 指定模型
)

# 查看模型性能
print(result.summary)
```

**适用场景**:
- 分类任务
- 回归任务
- 模型训练
- 性能评估

---

## 💡 实用技巧

### 自定义迭代次数

```python
# 覆盖默认的迭代次数
result = dslighting.analyze(
    data="data.csv",
    description="详细分析数据",
    model="gpt-4o",  # 指定模型
    max_iterations=5  # 默认是 2，这里改为 5
)
```

### 使用不同的工作流

```python
# 默认使用 'aide' 工作流，也可以指定其他工作流
result = dslighting.process(
    data="data.csv",
    description="处理数据",
    model="gpt-4o",  # 指定模型
    workflow="autokaggle"  # 使用 AutoKaggle 工作流
)
```

### 查看完整日志

```python
result = dslighting.analyze(
    data="data.csv",
    description="分析数据",
    model="gpt-4o",  # 指定模型
    verbose=True  # 显示详细日志
)
```

---

## 📂 数据文件格式

DSLighting 支持多种数据格式：

```bash
# 支持的文件格式
data.csv                    # CSV 文件
data.xlsx                   # Excel 文件
data.json                   # JSON 文件
data.parquet                # Parquet 文件

# 支持目录结构
data/
├── train.csv               # 训练数据
├── test.csv                # 测试数据
└── description.md          # 数据描述（可选）
```

---

## 🐛 常见问题

### Q1: 安装失败

**解决方法**:
```bash
# 使用升级的 pip
pip install --upgrade pip
pip install dslighting
```

### Q2: API 密钥错误

**解决方法**:
- 检查 `.env` 文件是否在正确位置
- 确认 API key 有效
- 确认 API base URL 正确

### Q3: 内存不足

**解决方法**:
```python
# 对大数据集使用采样
result = dslighting.analyze(
    data="large_data.csv",
    description="分析数据",
    model="gpt-4o",  # 指定模型
    max_iterations=1  # 减少迭代次数
)
```

### Q4: 需要可视化功能

**解决方法**:
```bash
pip install matplotlib seaborn
```

---

## 📖 进阶使用

### 完整工作流示例

```python
import dslighting

# 步骤 1: 分析数据
analysis = dslighting.analyze(
    data="data/titanic.csv",
    description="探索数据特征",
    model="gpt-4o"  # 指定模型
)
print("分析结果:", analysis.summary)

# 步骤 2: 处理数据
processed = dslighting.process(
    data="data/titanic.csv",
    description="清洗和预处理数据",
    model="gpt-4o"  # 指定模型
)
print("处理结果:", processed.summary)

# 步骤 3: 建模
model = dslighting.model(
    data="data/titanic.csv",
    description="训练预测模型",
    model="gpt-4o"  # 指定模型
)
print("模型结果:", model.summary)
```

### 使用 TaskContext 对象

```python
from dslighting import load_data, model

# 加载数据
context = load_data(
    data="data/titanic.csv",
    task="预测乘客生存",
    target="Survived"
)

# 建模
result = model(
    data=context,  # 使用 TaskContext 对象
    description="训练分类模型",
    model="gpt-4o"  # 指定模型
)
```

---

## 📞 获取帮助

- **文档**: https://luckyfan-cs.github.io/dslighting-web/
- **GitHub**: https://github.com/usail-hkust/dslighting
- **Issues**: https://github.com/usail-hkust/dslighting/issues

---

## 🎉 开始你的数据科学之旅！

现在你已经准备好使用 DSLighting 了！

```bash
# 运行示例
python main.py
```

**祝使用愉快！** 🚀
