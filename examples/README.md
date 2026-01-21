# DSLighting Examples

本目录包含 DSLighting 的使用示例，帮助你快速上手。

## 📚 示例列表

### 1. Kaggle Titanic 比赛 (推荐新手)

**目录**: `kaggle_titanic/`

展示如何使用 DSLighting 参加 Kaggle Titanic 比赛的经典示例。

**包含内容**:
- ✅ 完整的数据准备流程
- ✅ Registry 配置
- ✅ Grader 实现
- ✅ 运行脚本
- ✅ 详细文档

**适合**: 想要学习如何用 DSLighting 打 Kaggle 比赛的用户

**快速开始**:
```bash
cd examples/kaggle_titanic

# 1. 准备数据
python prepare_data.py

# 2. 运行示例
python run_titanic.py
```

详细说明请查看: [kaggle_titanic/README.md](kaggle_titanic/README.md)

## 🎯 通用工作流程

无论哪个比赛，基本流程都是相同的：

### 步骤 1: 安装 Kaggle API

```bash
pip install kaggle
```

### 步骤 2: 配置 API Token

```bash
# 下载 kaggle.json 后
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### 步骤 3: 下载比赛数据

```bash
# 替换为你的比赛名称
kaggle competitions download -c competition-name
```

### 步骤 4: 准备数据格式

将数据转换为 DSLighting 标准格式：

```
data/competitions/competition-name/
├── prepared/
│   ├── public/
│   │   ├── train.csv
│   │   ├── test.csv
│   │   └── sampleSubmission.csv
│   └── private/
│       └── test_answer.csv
```

### 步骤 5: 创建 Registry 配置

```bash
# 使用自动脚本创建
python examples/kaggle_titanic/add_kaggle_competition.py \
  --id competition-name \
  --name "Competition Display Name" \
  --metric accuracy
```

或手动创建配置文件 `dslighting/registry/competition-name/config.yaml`:

```yaml
id: competition-name
name: Competition Display Name
task_type: kaggle
dataset:
  answers: competition-name/prepared/private/test_answer.csv
  sample_submission: competition-name/prepared/public/sampleSubmission.csv
grader:
  name: accuracy
  grade_fn: grade:grade
```

### 步骤 6: 运行 DSLighting

```python
import dslighting

# 方式 1: 使用 task_id
result = dslighting.run_agent(
    model="openai/gpt-4",
    task_id="competition-name"
)

# 方式 2: 直接指定数据路径
result = dslighting.run_agent(
    model="openai/gpt-4",
    data_path="data/competitions/competition-name"
)
```

## 🛠️ 添加新比赛工具

快速添加新的 Kaggle 比赛：

```bash
python examples/kaggle_titanic/add_kaggle_competition.py \
  --id house-prices-advanced-regression-techniques \
  --name "House Prices - Advanced Regression Techniques" \
  --metric rmse
```

这会自动创建：
- Registry 配置文件
- Grader 模板
- Description 模板
- 数据准备脚本
- 必要的目录结构

## 📊 支持的任务类型

### 分类任务 (Classification)
**评估指标**: accuracy, f1, auc, logloss

**示例**: Titanic, Digit Recognizer

```yaml
grader:
  name: accuracy  # 或 f1, auc, logloss
```

### 回归任务 (Regression)
**评估指标**: rmse, mae, rmsle

**示例**: House Prices, Bike Sharing Demand

```yaml
grader:
  name: rmse  # 或 mae, rmsle
```

### 多标签分类 (Multi-label Classification)
**评估指标**: f1-score

**示例**: Toxic Comment Classification

```yaml
grader:
  name: f1
```

## 💡 最佳实践

### 1. 数据准备

- ✅ 确保 `train.csv` 包含特征和标签
- ✅ 确保 `test.csv` 只包含特征
- ✅ `sampleSubmission.csv` 格式与 Kaggle 要求一致
- ✅ 准备 `test_answer.csv` 用于本地验证

### 2. 选择 Workflow

| Workflow | 适用场景 | 特点 |
|----------|---------|------|
| `aide` | 简单任务，快速原型 | 迭代式代码生成 |
| `autokaggle` | 复杂 Kaggle 比赛 | 多阶段优化 |
| `data_interpreter` | 快速实验 | 代码执行循环 |
| `dsagent` | 结构化任务 | 操作符驱动 |

### 3. 选择模型

| 模型 | 性能 | 成本 | 速度 |
|------|------|------|------|
| `gpt-4` | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| `gpt-3.5-turbo` | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| `deepseek-chat` | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

### 4. 调整参数

```python
result = dslighting.run_agent(
    model="openai/gpt-4",
    task_id="competition-name",
    workflow="aide",
    max_iterations=10,      # 最大迭代次数
    timeout=3600,           # 超时时间（秒）
    budget=10.0,            # 最大预算（美元）
)
```

## 📖 更多资源

- [DSLighting 完整文档](../README.md)
- [API 参考](../docs/API.md)
- [Workflow 指南](../claude_doc/WORKFLOW_QUICK_REFERENCE.md)
- [Kaggle 官方文档](https://www.kaggle.com/docs)

## 🤝 贡献

欢迎提交 PR 添加更多比赛示例！

## 📄 许可证

MIT License
