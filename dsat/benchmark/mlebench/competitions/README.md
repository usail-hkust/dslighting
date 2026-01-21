# MLE-Bench 比赛目录

本目录包含所有 MLE-Bench 格式的比赛定义。

## 📚 目录结构说明

MLE-Bench 使用**两个独立的目录**来组织比赛：

```
1️⃣  比赛注册目录（本目录）
   /path/to/data_science_agent_toolkit/mlebench/competitions/
   └── <competition-id>/
       ├── config.yaml         ✓ 必需 - 比赛配置
       ├── description.md      ✓ 必需 - 比赛描述
       ├── grade.py            ✓ 必需 - 评分函数
       ├── prepare.py          ✓ 必需 - 数据准备函数
       ├── checksums.yaml      ✓ 必需 - 数据校验
       └── leaderboard.csv     ✓ 必需 - 排行榜

2️⃣  数据集目录
   /path/to/mlebench-data/
   └── <competition-id>/
       ├── prepare.py          # 便捷准备脚本
       ├── raw/                # 原始数据
       └── prepared/           # 准备后的数据
           ├── public/         # 参赛者可见
           └── private/        # 用于评分
```

详细说明请参考：[/path/to/mle/competitions/README.md](../../mle/competitions/README.md)

## 📊 已有比赛统计

### 按数据来源分类

#### 1. DSAgentBench 数据集（时间序列）

| 比赛 ID | 名称 | 任务类型 | 训练样本 | 测试样本 | 评估指标 | 难度 |
|---------|------|---------|----------|----------|----------|------|
| handwriting | Handwriting Time Series Classification | 分类（26类） | 150 | 850 | Accuracy | Easy |
| ethanol-concentration | Ethanol Concentration Classification | 分类（4类） | 261 | 263 | Accuracy | Easy |
| ili | ILI Time Series Forecasting | 多变量预测 | 617 | 170 | MSE/MAE | Medium |

**特点**：
- 数据模态：时间序列
- 格式：.ts 文件（sktime）或 numpy arrays
- 用途：完整的机器学习 pipeline 比赛

#### 2. DABench 数据集（数据分析任务）

DABench 任务是简单的数据分析任务，对应 ML pipeline 中的单个子过程。

**已转换的示例**：

| 比赛 ID | 任务 | 概念 | 难度 | 数据文件 |
|---------|------|------|------|----------|
| dabench-0-mean-fare | 计算平均票价 | Summary Statistics | Easy | test_ave.csv |

**待转换任务统计**（共约 200+ 个任务）：

- **Summary Statistics**: 均值、中位数、标准差等
- **Feature Engineering**: 特征生成、转换
- **Correlation Analysis**: 相关性分析
- **Distribution Analysis**: 分布分析、正态性检验
- **Outlier Detection**: 异常值检测
- **Machine Learning**: 模型训练、预测、评估
- **Data Preprocessing**: 数据清洗、缺失值处理

**难度分布**：
- Easy: ~100 个任务
- Medium: ~70 个任务
- Hard: ~30 个任务

### 总体统计

```
总比赛数: 4 (3 DSAgentBench + 1 DABench)
数据模态: Time Series (3), Tabular (1)
任务类型: 分类 (2), 预测 (1), 数据分析 (1)
```

## 🔄 批量转换 DABench 任务

### 使用转换脚本

位置：`/path/to/convert_dabench_to_mlebench.py`

#### 1. 列出所有可用任务

```bash
python convert_dabench_to_mlebench.py --list
```

示例输出：
```
Available DABench tasks:
================================================================================
Task   0 [easy  ]: Calculate the mean fare paid by the passengers....
Task   5 [medium]: Generate a new feature called "FamilySize"...
Task   6 [medium]: Create a new column called "AgeGroup"...
...
================================================================================
Total: 200+ tasks
```

#### 2. 转换单个或多个任务

```bash
# 转换单个任务
python convert_dabench_to_mlebench.py --task-ids 0

# 转换多个任务
python convert_dabench_to_mlebench.py --task-ids 0 5 6 7

# Dry run (不创建文件，仅测试)
python convert_dabench_to_mlebench.py --task-ids 0 --dry-run
```

#### 3. 批量转换所有任务

```bash
# 转换所有 DABench 任务（约 200+ 个）
python convert_dabench_to_mlebench.py --all

# Dry run 查看将创建什么
python convert_dabench_to_mlebench.py --all --dry-run
```

### 转换后的结构

每个 DABench 任务会创建：

**比赛注册目录**：
```
mlebench/competitions/dabench-<id>-<keywords>/
├── config.yaml
├── description.md
├── grade.py
├── prepare.py
├── leaderboard.csv
└── checksums.yaml
```

**数据集目录**：
```
DSFlow/data/competitions/dabench-<id>-<keywords>/
├── prepare.py
├── raw/
│   └── <data_file>.csv
└── prepared/
    ├── public/
    │   ├── train.csv
    │   └── sample_submission.csv
    └── private/
        └── answer.csv
```

### 准备转换后的数据

```bash
# 进入数据集目录
cd /path/to/mlebench-data/dabench-<id>-<keywords>

# 运行准备脚本
python prepare.py
```

## 🚀 运行比赛

### 运行单个比赛

```bash
cd /path/to/data_science_agent_toolkit

conda run -n dstool python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --mle-data-dir "/path/to/mlebench-data" \
  --llm-model openai/deepseek-ai/DeepSeek-V3.1-Terminus \
  --mle-competitions <competition-id>
```

### 批量运行多个比赛

```bash
# 运行多个 DABench 任务
for task_id in 0 5 6; do
  python run_benchmark.py \
    --workflow aide \
    --benchmark mle \
    --mle-data-dir "/path/to/mlebench-data" \
    --llm-model openai/deepseek-ai/DeepSeek-V3.1-Terminus \
    --mle-competitions dabench-${task_id}-*
done
```

## 📝 创建新比赛

### 方式 1: 从 DABench 转换（推荐用于数据分析任务）

使用上述转换脚本自动创建。

### 方式 2: 手动创建（完整 ML 任务）

1. **创建比赛定义**

```bash
cd /path/to/data_science_agent_toolkit
mkdir -p mlebench/competitions/<competition-id>
```

创建 6 个必需文件：
- `config.yaml` - 比赛配置
- `description.md` - 比赛描述
- `grade.py` - 评分函数
- `prepare.py` - 数据准备函数
- `leaderboard.csv` - 排行榜
- `checksums.yaml` - 数据校验

2. **准备数据**

```bash
cd /path/to/mlebench-data
mkdir -p <competition-id>/raw

# 复制原始数据
cp /path/to/data <competition-id>/raw/

# 创建便捷准备脚本
cat > <competition-id>/prepare.py <<'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
import importlib.util

prepare_file = Path('/path/to/data_science_agent_toolkit/mlebench/competitions/<competition-id>/prepare.py')
spec = importlib.util.spec_from_file_location("prepare_module", prepare_file)
prepare_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_module)
prepare_fn = prepare_module.prepare

current_dir = Path(__file__).parent
raw_dir = current_dir / 'raw'
public_dir = current_dir / 'prepared' / 'public'
private_dir = current_dir / 'prepared' / 'private'

public_dir.mkdir(parents=True, exist_ok=True)
private_dir.mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    print(f"Preparing <competition-id>...")
    prepare_fn(raw_dir, public_dir, private_dir)
    print("✓ Done!")
EOF

# 运行准备
python <competition-id>/prepare.py
```

详细指南：[/path/to/mle/competitions/README.md](../../mle/competitions/README.md)

## ⚙️ 数据格式要求

### CSV 格式是强制性的

MLE-Bench 框架**只接受 CSV 格式**的提交和答案文件：

```python
# 框架代码检查
submission_exists = (
    path_to_submission.is_file() and
    path_to_submission.suffix.lower() == ".csv"
)
```

### DABench 特殊格式

DABench 任务使用特殊的答案格式：

```
@key1[value1] @key2[value2] ...
```

示例：
```
@mean_fare[34.65]
@correlation_coefficient[0.21]
@mean_fare_child[31.09] @mean_fare_adult[35.17]
```

### 多维数据处理

对于多维输出（如时间序列预测），需要展平为 2D CSV：

```python
# 3D (N, 24, 7) -> 2D (N, 168)
predictions_flat = predictions.reshape(len(predictions), -1)
df = pd.DataFrame(predictions_flat, columns=[f'pred_{i}' for i in range(168)])
df.insert(0, 'id', range(len(predictions)))
df.to_csv('submission.csv', index=False)
```

## 🔍 测试比赛

### 测试评分功能

创建测试脚本 `test_grading.py`：

```python
import pandas as pd
import importlib.util
from pathlib import Path

# 加载 grade 模块
grade_file = Path('mlebench/competitions/<competition-id>/grade.py')
spec = importlib.util.spec_from_file_location("grade_module", grade_file)
grade_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grade_module)
grade_fn = grade_module.grade

# 加载答案
answers = pd.read_csv('DSFlow/data/competitions/<competition-id>/prepared/private/answer.csv')

# 测试完美提交
perfect_submission = answers.copy()
score = grade_fn(perfect_submission, answers)
print(f"Perfect submission score: {score} (expected: 1.0)")

# 测试错误提交
wrong_submission = pd.DataFrame({'id': [0], 'answer': ['@key[wrong_value]']})
score = grade_fn(wrong_submission, answers)
print(f"Wrong submission score: {score} (expected: 0.0)")
```

## 📖 相关文档

### 核心文档

- **完整指南**: `/path/to/mle/competitions/README.md`
  - 详细的创建步骤
  - 两个目录的关系
  - 常见问题解答
  - 示例代码

- **比赛索引**: `/path/to/mle/competitions/INDEX.md`
  - 所有比赛列表
  - 对比表格

### 特定比赛文档

每个比赛可能包含：
- `README.md` - 比赛说明
- `FIXES.md` - 修复记录（如有）

例如：
- `/path/to/mlebench-data/ili/README.md`
- `/path/to/mlebench-data/ili/FIXES.md`

## 🎯 快速开始示例

### 示例 1: 转换并运行一个 DABench 任务

```bash
# 1. 转换任务
python convert_dabench_to_mlebench.py --task-ids 0

# 2. 准备数据
cd /path/to/mlebench-data/dabench-0-mean-fare
python prepare.py

# 3. 测试评分
python test_grading.py

# 4. 运行比赛
cd /path/to/data_science_agent_toolkit
conda run -n dstool python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --mle-data-dir "/path/to/mlebench-data" \
  --llm-model openai/deepseek-ai/DeepSeek-V3.1-Terminus \
  --mle-competitions dabench-0-mean-fare
```

### 示例 2: 批量转换 Easy 难度的任务

```bash
# 列出所有 easy 任务
python convert_dabench_to_mlebench.py --list | grep easy

# 选择一些 easy 任务转换
python convert_dabench_to_mlebench.py --task-ids 0 9 10 18 19 24 25 26

# 批量准备数据
for comp_id in dabench-*-*/; do
  cd "/path/to/mlebench-data/$comp_id"
  echo "Preparing $comp_id..."
  python prepare.py
done
```

## 🐛 常见问题

### Q1: 转换脚本找不到数据文件

**错误**: `⚠ Warning: Data file not found: /path/to/DABench/da-dev-tables/xxx.csv`

**解决**: 确保 DABench 数据已下载：
```bash
cd /path/to/DABench
python download_dabench.py
```

### Q2: 导入模块失败

**错误**: `ModuleNotFoundError: No module named 'mlebench.competitions.xxx'`

**解决**: 使用 `importlib.util` 直接从文件路径加载：
```python
import importlib.util
spec = importlib.util.spec_from_file_location("module", "/path/to/file.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

### Q3: 比赛 ID 命名冲突

如果转换脚本生成的比赛 ID 重复，可以手动修改：
```bash
mv mlebench/competitions/dabench-X-keywords \
   mlebench/competitions/dabench-X-keywords-v2
```

并更新 `config.yaml` 中的 `id` 字段。

## 📊 贡献统计

```
DSAgentBench 比赛: 3 个
  - handwriting (2024-10-27)
  - ethanol-concentration (2024-10-27)
  - ili (2024-10-27, fixed CSV format)

DABench 比赛: 1+ 个
  - dabench-0-mean-fare (2024-10-30, 测试成功)
  - 待转换: ~200 个任务

总计: 4+ 个比赛
```

## 🔗 相关链接

- **MLE-Bench 官方仓库**: https://github.com/openai/mle-bench
- **DABench 数据集**: `/path/to/DABench`
- **DSAgentBench 数据集**: `/path/to/dsagentbench`

## 📝 更新日志

- **2024-10-30**: 添加 DABench 批量转换脚本和文档
- **2024-10-30**: 完成 dabench-0-mean-fare 测试
- **2024-10-27**: 创建初始 README
- **2024-10-27**: 添加 DSAgentBench 3 个比赛
- **2024-10-27**: 修复 ili 比赛 CSV 格式问题

## 📧 联系方式

如有问题或建议，请参考相关文档或查看示例比赛的实现。
