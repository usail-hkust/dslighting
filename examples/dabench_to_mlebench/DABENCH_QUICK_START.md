# DABench 转换快速开始

## 🚀 5 分钟快速上手

### 步骤 1: 列出所有任务

```bash
cd /path/to
python convert_dabench_to_mlebench.py --list
```

### 步骤 2: 选择并转换任务

```bash
# 转换单个任务 (Task 0: 计算平均票价)
python convert_dabench_to_mlebench.py --task-ids 0

# 转换多个任务
python convert_dabench_to_mlebench.py --task-ids 0 5 6 9 10

# Dry run 测试
python convert_dabench_to_mlebench.py --task-ids 0 --dry-run
```

### 步骤 3: 准备数据

```bash
cd /path/to/mlebench-data/dabench-0-mean-fare
python prepare.py
```

### 步骤 4: 测试评分（可选）

```bash
cd /path/to/mlebench-data/dabench-0-mean-fare
python test_grading.py  # 如果创建了测试脚本
```

### 步骤 5: 运行比赛

```bash
cd /path/to/data_science_agent_toolkit

conda run -n dstool python run_benchmark.py \
  --workflow aide \
  --benchmark mle \
  --mle-data-dir "/path/to/mlebench-data" \
  --llm-model openai/deepseek-ai/DeepSeek-V3.1-Terminus \
  --mle-competitions dabench-0-mean-fare
```

## 📋 常用命令

### 批量转换

```bash
# 转换所有 Easy 任务的一部分
python convert_dabench_to_mlebench.py --task-ids \
  0 9 10 18 19 24 25 26 32 33 55 56 57 58

# 转换所有任务（约 200+ 个）
python convert_dabench_to_mlebench.py --all
```

### 批量准备数据

```bash
# 准备所有转换后的任务
cd /path/to/mlebench-data

for dir in dabench-*/; do
    echo "Preparing $dir..."
    cd "$dir"
    python prepare.py
    cd ..
done
```

### 查看已转换任务

```bash
# 查看比赛注册目录
ls -la /path/to/data_science_agent_toolkit/mlebench/competitions/ | grep dabench

# 查看数据集目录
ls -la /path/to/mlebench-data/ | grep dabench
```

## 📂 文件位置

| 内容 | 位置 |
|------|------|
| **转换脚本** | `/path/to/convert_dabench_to_mlebench.py` |
| **比赛注册** | `/path/to/data_science_agent_toolkit/mlebench/competitions/` |
| **数据集** | `/path/to/mlebench-data/` |
| **主文档** | `/path/to/data_science_agent_toolkit/mlebench/competitions/README.md` |
| **总结** | `/path/to/DABENCH_CONVERSION_SUMMARY.md` |

## 🎯 推荐任务

### 初学者（Easy 难度）

| Task ID | 描述 | 概念 |
|---------|------|------|
| 0 | 计算平均票价 | Summary Statistics |
| 9 | 计算收盘价均值 | Summary Statistics |
| 10 | 检验正态分布 | Distribution Analysis |
| 24 | 计算平均年龄 | Summary Statistics |
| 25 | BMI 分布检验 | Distribution Analysis |
| 26 | 相关系数计算 | Correlation Analysis |

### 中级（Medium 难度）

| Task ID | 描述 | 概念 |
|---------|------|------|
| 5 | 特征工程+相关性 | Feature Engineering, Correlation |
| 6 | 年龄分组统计 | Feature Engineering, Statistics |
| 8 | 分布分析 | Distribution Analysis |
| 11 | 相关系数+显著性 | Correlation Analysis |
| 27 | 异常值检测 | Outlier Detection |

### 高级（Hard 难度）

| Task ID | 描述 | 概念 |
|---------|------|------|
| 7 | 线性回归预测 | Machine Learning |
| 23 | 时间序列预测 | Machine Learning |
| 28 | 数据预处理 | Data Preprocessing |
| 30 | 模型训练评估 | Machine Learning |

## ⚡ 一键转换示例

### 转换所有 Easy 任务（示例子集）

```bash
python convert_dabench_to_mlebench.py --task-ids \
  0 9 10 18 19 24 25 26 32 33 55 56 57 58 59
```

### 转换分类任务

```bash
# Summary Statistics
python convert_dabench_to_mlebench.py --task-ids 0 9 18 24 32

# Distribution Analysis
python convert_dabench_to_mlebench.py --task-ids 10 19 25 33

# Correlation Analysis
python convert_dabench_to_mlebench.py --task-ids 11 26 34 57
```

## 🔍 检查转换结果

```bash
# 检查任务 0
cd /path/to/data_science_agent_toolkit/mlebench/competitions/dabench-0-mean-fare
ls -la

# 应该看到:
# - config.yaml
# - description.md
# - grade.py
# - prepare.py
# - leaderboard.csv
# - checksums.yaml

# 检查数据
cd /path/to/mlebench-data/dabench-0-mean-fare
ls -la prepared/public/
ls -la prepared/private/

# 应该看到:
# public/: train.csv, sample_submission.csv
# private/: answer.csv
```

## 🐛 快速故障排除

### 问题 1: 找不到数据文件

```bash
# 确保 DABench 数据已下载
cd /path/to/DABench
ls da-dev-tables/  # 应该看到很多 .csv 文件
```

### 问题 2: 准备脚本失败

```bash
# 检查 raw 目录是否有数据
ls /path/to/mlebench-data/dabench-*/raw/

# 手动运行框架的 prepare 函数
cd /path/to/data_science_agent_toolkit
python -c "
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('prepare', 'mlebench/competitions/dabench-0-mean-fare/prepare.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
"
```

### 问题 3: 评分测试失败

```bash
# 检查答案文件
cat /path/to/mlebench-data/dabench-0-mean-fare/prepared/private/answer.csv

# 应该看到正确的格式:
# id,answer
# 0,@mean_fare[34.65]
```

## 📖 更多信息

- **完整文档**: `/path/to/data_science_agent_toolkit/mlebench/competitions/README.md`
- **详细总结**: `/path/to/DABENCH_CONVERSION_SUMMARY.md`
- **MLE-Bench 指南**: `/path/to/mle/competitions/README.md`

## 💡 提示

1. **先用 dry-run 测试**: 使用 `--dry-run` 检查转换结果
2. **批量准备数据**: 转换后批量运行 prepare.py
3. **选择性转换**: 不需要一次转换所有任务，可以按需转换
4. **检查答案格式**: 转换后检查 answer.csv 格式是否正确

---

**快速帮助**: `python convert_dabench_to_mlebench.py --help`
