# DSLighting + Kaggle 完整示例：Titanic 比赛

本示例展示如何使用 DSLighting 包来参加 Kaggle 比赛，以 Titanic 比赛为例。

## 🎯 流程概览

```
1. 安装 Kaggle API → 2. 下载数据 → 3. 准备标准格式 → 4. 配置 Registry → 5. 运行 DSLighting
```

## 📋 前置要求

- Python 3.10+
- DSLighting 已安装
- Kaggle 账号和 API Token

## 🚀 快速开始

### 步骤 1: 安装 Kaggle API

```bash
pip install kaggle
```

### 步骤 2: 配置 Kaggle API Token

1. 登录 Kaggle: https://www.kaggle.com/
2. 进入账户设置 → API → Create New API Token
3. 下载 `kaggle.json` 文件
4. 将文件移动到正确位置：

```bash
# Linux/Mac
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows
# 创建文件夹: C:\Users\<username>\.kaggle
# 将 kaggle.json 移动到该文件夹
```

### 步骤 3: 下载并准备数据

运行自动脚本：

```bash
python prepare_data.py
```

或手动执行：

```bash
# 下载 Kaggle 数据
kaggle competitions download -c titanic

# 解压数据
unzip titanic.zip -d data/raw/

# 准备标准格式
python scripts/prepare_titanic_data.py
```

### 步骤 4: 创建 Registry 配置

Registry 配置文件位于 `dslighting/registry/titanic/config.yaml`：

```yaml
id: titanic
name: Titanic - Machine Learning from Disaster
competition_type: simple
task_type: kaggle
awards_medals: true

dataset:
  answers: titanic/prepared/private/test_answer.csv
  sample_submission: titanic/prepared/public/sampleSubmission.csv

grader:
  name: accuracy
  grade_fn: grade:grade
```

### 步骤 5: 运行 DSLighting

#### 方式 1: 使用 Python API

```python
import dslighting

# 加载数据
data = dslighting.load_data("data/competitions/titanic")

# 查看数据信息
print(data.show())

# 运行 Agent
agent = dslighting.Agent()
result = agent.run(
    data,
    model="openai/gpt-4",  # 或其他模型
    workflow="aide"  # 可选: aide, autokaggle, data_interpreter
)

# 查看结果
print(f"Score: {result.score}")
print(f"Submission: {result.output_path}")
```

#### 方式 2: 使用命令行

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --task-id titanic \
  --llm-model openai/gpt-4
```

## 📁 标准数据格式

DSLighting 使用 MLE-Bench 标准格式：

```
data/competitions/titanic/
├── prepared/
│   ├── public/           # 训练数据
│   │   ├── train.csv     # 特征 + 标签
│   │   └── test.csv      # 测试特征（无标签）
│   └── private/          # 私有数据（用于验证）
│       └── test_answer.csv  # 测试集答案
└── sampleSubmission.csv  # 提交格式示例
```

### 关键文件说明

1. **train.csv**: 训练集，包含所有特征和标签
2. **test.csv**: 测试集，只包含特征，需要预测标签
3. **test_answer.csv**: 测试集的真实标签（用于本地验证）
4. **sampleSubmission.csv**: 提交格式示例

## 🔧 自定义你的 Kaggle 比赛

### 1. 下载新比赛数据

```bash
# 替换为你的比赛名称
kaggle competitions download -c competition-name

# 示例：House Prices
kaggle competitions download -c house-prices-advanced-regression-techniques
```

### 2. 准备数据格式

创建 `prepare_[competition].py` 脚本：

```python
import pandas as pd
from pathlib import Path

def prepare_competition_data():
    # 读取原始数据
    data_dir = Path("data/raw/competition-name")
    prepared_dir = Path("data/competitions/competition-name/prepared")

    # 创建目录
    prepared_dir.mkdir(parents=True, exist_ok=True)
    (prepared_dir / "public").mkdir(exist_ok=True)
    (prepared_dir / "private").mkdir(exist_ok=True)

    # 读取数据
    train = pd.read_csv(data_dir / "train.csv")
    test = pd.read_csv(data_dir / "test.csv")
    sample_submission = pd.read_csv(data_dir / "sample_submission.csv")

    # 保存训练数据（包含标签）
    train.to_csv(prepared_dir / "public" / "train.csv", index=False)

    # 保存测试数据（无标签）
    test.to_csv(prepared_dir / "public" / "test.csv", index=False)

    # 保存提交示例
    sample_submission.to_csv(prepared_dir / "public" / "sampleSubmission.csv", index=False)

    # 注意：test_answer.csv 需要你自己创建或从 Kaggle 下载
    # 或者使用验证集的一部分作为 test_answer

    print(f"✅ 数据准备完成: {prepared_dir}")

if __name__ == "__main__":
    prepare_competition_data()
```

### 3. 创建 Registry 配置

创建 `dslighting/registry/competition-name/config.yaml`：

```yaml
id: competition-name
name: Competition Display Name
competition_type: simple
task_type: kaggle
awards_medals: false

dataset:
  answers: competition-name/prepared/private/test_answer.csv
  sample_submission: competition-name/prepared/public/sampleSubmission.csv

grader:
  name: metric-name  # accuracy, rmse, f1, etc.
  grade_fn: grade:grade
```

### 4. 创建 Grader（可选）

如果比赛使用特殊评估指标，创建 grader：

```python
# dslighting/registry/competition-name/grade.py
import pandas as pd
import numpy as np

def grade(submission_path: str, answer_path: str) -> float:
    """评估提交结果"""
    submission = pd.read_csv(submission_path)
    answers = pd.read_csv(answer_path)

    # 计算你的指标
    score = your_metric_function(submission, answers)

    return score

def your_metric_function(preds, true):
    """自定义评估函数"""
    # 示例：准确率
    return (preds['target'] == true['target']).mean()
```

### 5. 运行

```python
import dslighting

# 方式 1: 使用 task_id（如果已配置 registry）
result = dslighting.run_agent(
    model="openai/gpt-4",
    task_id="competition-name"
)

# 方式 2: 直接指定数据路径
result = dslighting.run_agent(
    model="openai/gpt-4",
    data_path="data/competitions/competition-name",
    registry_dir="dslighting/registry"  # 可选
)
```

## 📊 支持的评估指标

| 指标 | 适用场景 |
|------|---------|
| accuracy | 分类问题（类别均衡）|
| f1 | 分类问题（类别不平衡）|
| auc | 二分类问题 |
| rmse | 回归问题 |
| mae | 回归问题 |
| rmsle | 回归问题（对数误差）|
| logloss | 概率预测 |

## 💡 最佳实践

### 1. 数据准备

- ✅ 确保 `train.csv` 包含所有特征和标签
- ✅ 确保 `test.csv` 只包含特征
- ✅ `sampleSubmission.csv` 格式完全匹配 Kaggle 要求
- ✅ 如果可能，准备 `test_answer.csv` 用于本地验证

### 2. 配置 Registry

- ✅ 使用清晰的 `task_id`（通常是 Kaggle competition slug）
- ✅ 指定正确的评估指标
- ✅ 添加任务描述

### 3. 运行 Agent

- ✅ 选择合适的 workflow：
  - `aide`: 简单任务，快速迭代
  - `autokaggle`: 复杂 Kaggle 比赛，多阶段优化
  - `data_interpreter`: 快速代码执行
- ✅ 设置合适的模型：
  - `gpt-4`: 最佳性能
  - `gpt-3.5-turbo`: 成本效益平衡
  - DeepSeek 等：开源替代

### 4. 提交到 Kaggle

```bash
# DSLighting 会生成 submission 文件
# 通常位于: runs/benchmark_results/.../submission.csv

# 提交到 Kaggle
kaggle competitions submit -c competition-name \
  -f submission.csv \
  -m "Generated by DSLighting"
```

## 🎓 完整工作流示例

```bash
# 1. 下载比赛数据
kaggle competitions download -c titanic

# 2. 准备数据
python prepare_data.py

# 3. 运行 DSLighting
python run_titanic.py

# 4. 提交到 Kaggle
kaggle competitions submit -c titanic \
  -f runs/benchmark_results/aide_on_mle/openai__gpt-4/latest/submission.csv \
  -m "DSLighting Auto Submission"
```

## 🔍 常见问题

### Q: 如何获取 test_answer.csv？

A: 有几种方式：
1. 从 Kaggle Discussion 板找基准答案
2. 使用交叉验证，将训练集分割
3. 先用部分训练数据作为测试集进行验证

### Q: Agent 运行时间太长怎么办？

A:
1. 减少最大迭代次数
2. 使用更快的模型（如 gpt-3.5-turbo）
3. 限制数据集大小用于测试

### Q: 如何查看 Agent 的详细日志？

A: 日志保存在 `runs/benchmark_results/` 目录，查看：
- `logs/execution.log`: 完整执行日志
- `summary.json`: 结果摘要
- `artifacts/`: 生成的代码和模型

### Q: 可以使用本地模型吗？

A: 可以！只需配置模型名称，DSLighlighting 支持通过 LiteLLM 接入各种模型。

## 📚 相关文档

- [DSLighting 完整文档](../../README.md)
- [API 参考](../../docs/API.md)
- [Workflow 指南](../../claude_doc/WORKFLOW_QUICK_REFERENCE.md)

## 🤝 贡献

欢迎提交 PR 添加更多比赛示例！

## 📄 许可证

MIT License
