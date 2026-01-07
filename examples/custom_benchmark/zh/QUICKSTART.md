# 快速开始指南

30 秒开始，5 分钟定制你的第一个数据科学 Benchmark。

---

## 🚀 30 秒体验

```bash
cd examples/custom_benchmark
bash run_example.sh
```

**自动完成**:
1. ✓ 生成 100 条模拟房价数据
2. ✓ 准备训练集（80 条）和测试集（20 条）
3. ✓ 运行模拟 Agent 生成预测
4. ✓ 计算 RMSE 分数

**结果**: `test_results/` 目录包含提交文件和评分结果

---

## 📖 5 分钟理解结构

### 目录结构一览

```
custom_benchmark/
├── competitions/           # 比赛注册目录
│   └── custom-house-price-prediction/
│       ├── config.yaml            # 配置: 任务 ID、评分函数等
│       ├── description.md         # 任务说明
│       ├── grade.py               # 评分逻辑: RMSE 计算
│       └── prepare.py             # 数据准备: 训练/测试分离
│
└── data/                   # 数据集目录
    └── custom-house-price-prediction/
        ├── raw/houses.csv         # 原始数据
        └── prepared/
            ├── public/train.csv   # 训练数据（Agent 可见）
            └── private/answer.csv # 测试答案（评分用）
```

### 三个关键概念

| 概念 | 文件 | 作用 |
|------|------|------|
| **注册** | `competitions/*/config.yaml` | 定义任务元数据和处理管道 |
| **准备** | `competitions/*/prepare.py` | 原始数据 → 公开/私有数据 |
| **评分** | `competitions/*/grade.py` | 提交文件 → 分数 |

---

## 🔧 5 分钟定制

### 步骤 1: 修改数据生成

编辑 `prepare_example_data.py`:

```python
# 增加样本数量
df = generate_house_data(n_samples=500)  # 从 100 → 500

# 增加特征
data['bathrooms'] = np.random.randint(1, 4, n_samples)
data['garage'] = np.random.choice([0, 1, 2], n_samples)
```

### 步骤 2: 调整评分逻辑

编辑 `competitions/custom-house-price-prediction/grade.py`:

```python
# 从 RMSE 改为 MAE
def grade(submission, answers):
    mae = np.mean(np.abs(submission['predicted_price'] - answers['actual_price']))
    return mae
```

### 步骤 3: 更新任务描述

编辑 `competitions/custom-house-price-prediction/description.md`:

```markdown
## 新增特征
- bathrooms: 浴室数量（1-3）
- garage: 车库数量（0-2）

## 评分标准
MAE（Mean Absolute Error）- 越低越好
```

### 步骤 4: 重新生成和测试

```bash
# 1. 重新生成数据
python prepare_example_data.py

# 2. 重新准备数据集
cd competitions/custom-house-price-prediction
python prepare.py
cd ../..

# 3. 测试
python custom_benchmark.py
```

---

## 🏗️ 创建新任务

### 模板：分类任务示例

```bash
# 1. 创建目录
mkdir -p competitions/my-classification-task
mkdir -p data/my-classification-task/raw

# 2. 创建 config.yaml
cat > competitions/my-classification-task/config.yaml << EOF
id: my-classification-task
name: My Classification Challenge
competition_type: kaggle
grader:
  name: accuracy
  grade_fn: competitions.my-classification-task.grade:grade
preparer: competitions.my-classification-task.prepare:prepare
EOF

# 3. 创建 grade.py
cat > competitions/my-classification-task/grade.py << 'EOF'
import pandas as pd

def grade(submission, answers):
    accuracy = (submission['predicted'] == answers['actual']).mean()
    return accuracy
EOF
```

### 完整模板

参考 `competitions/custom-house-price-prediction/` 目录，复制并修改以下文件：
- `config.yaml` - 更新 ID 和名称
- `description.md` - 描述你的任务
- `prepare.py` - 实现数据准备逻辑
- `grade.py` - 实现评分逻辑

---

## 🔗 集成到主框架

### 选项 A: 独立运行（推荐用于测试）

```bash
python custom_benchmark.py
```

### 选项 B: 集成到 `run_benchmark.py`

1. 编辑 `run_benchmark.py`:
```python
from examples.custom_benchmark.custom_benchmark import HousePriceBenchmark

BENCHMARK_CLASSES = {
    "mle": MLEBenchmark,
    "house_price": HousePriceBenchmark,  # 添加
}
```

2. 运行:
```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark house_price \
  --log-path ./runs/house_price_results
```

---

## 📊 查看结果

### 评分输出

```bash
✓ RMSE: 25432.18
```

### 结果 CSV

```csv
task_id,submission_path,rmse_score,cost,submission_valid,error_message
custom-house-price-prediction,./test_results/submission_xxx.csv,25432.18,0.0,True,
```

### 提交文件

```csv
house_id,predicted_price
81,287534.12
82,345123.45
...
```

---

## ⚡ 常用命令

```bash
# 完整流程
bash run_example.sh

# 仅生成数据
python prepare_example_data.py

# 仅准备数据集
cd competitions/custom-house-price-prediction && python prepare.py

# 测试 Benchmark
python custom_benchmark.py

# 测试评分函数
cd competitions/custom-house-price-prediction && python grade.py
```

---

## 🐛 故障排除

### 问题: "竞赛数据目录不存在"

**解决**:
```bash
python prepare_example_data.py
cd competitions/custom-house-price-prediction
python prepare.py
```

### 问题: "评分失败"

**检查**:
1. 提交文件是否存在
2. 列名是否正确：`house_id`, `predicted_price`
3. house_id 是否与测试集一致

**调试**:
```bash
python -c "
import pandas as pd
sub = pd.read_csv('test_results/submission_xxx.csv')
ans = pd.read_csv('data/custom-house-price-prediction/prepared/private/answer.csv')
print('Submission columns:', sub.columns.tolist())
print('Answer columns:', ans.columns.tolist())
print('Submission shape:', sub.shape)
print('Answer shape:', ans.shape)
"
```

---

## 📚 下一步

- 📖 阅读 [README.md](README.md) 了解详细结构
- 🔍 查看 `competitions/*/` 文件了解实现细节
- 🚀 参考 `dsat/benchmark/mle.py` 学习生产级代码
- 💡 创建自己的任务并分享！

---

**提示**: 遇到问题？检查日志输出或运行 `python grade.py` 测试评分函数。
