# 自定义 Benchmark 示例

本示例演示如何为 dslighting 框架添加自定义数据科学 benchmark，采用完整的 DABench 风格结构。

## 📋 目录

- [概览](#概览)
- [示例任务](#示例任务)
- [目录结构](#目录结构)
- [核心组件](#核心组件)
- [快速开始](#快速开始)
- [扩展指南](#扩展指南)
- [集成到框架](#集成到框架)

---

## 概览

### 什么是 dslighting Benchmark?

Benchmark 是 dslighting 框架中用于评估 AI Agent 在特定任务上表现的组件。一个完整的 benchmark包括：
- **任务定义**: 描述要解决的问题
- **数据集**: 训练数据和测试数据
- **评分函数**: 量化 Agent 的表现
- **工作流接口**: 与 dslighting Agent 交互

### 为什么需要自定义 Benchmark?

- ✅ 评估 Agent 在特定领域的能力
- ✅ 标准化测试流程和评分标准
- ✅ 复现实验结果
- ✅ 对比不同 Agent 的表现

---

## 示例任务

本示例实现了一个**房价预测 Benchmark**：

- **任务类型**: 回归
- **输入**: 房屋特征（面积、房间数、年龄、位置评分）
- **输出**: 预测的房价（美元）
- **评分**: RMSE（Root Mean Squared Error）

这是一个典型的数据科学任务，适合演示完整的数据准备→训练→评分流程。

---

## 目录结构

```
examples/custom_benchmark/
├── README.md                                    # 本文档
├── QUICKSTART.md                                # 快速开始指南
├── prepare_example_data.py                      # 数据生成脚本
├── custom_benchmark.py                          # Benchmark 类实现
├── run_example.sh                               # 一键运行脚本
│
├── competitions/                                # 比赛注册目录
│   └── custom-house-price-prediction/
│       ├── config.yaml                          # 比赛配置
│       ├── description.md                       # 任务描述
│       ├── grade.py                             # 评分函数
│       ├── prepare.py                           # 数据准备函数
│       ├── leaderboard.csv                      # 示例排行榜
│       └── checksums.yaml                       # 数据校验
│
└── data/                                        # 数据集目录
    └── custom-house-price-prediction/
        ├── raw/                                 # 原始数据
        │   └── houses.csv
        └── prepared/                            # 准备后的数据
            ├── public/                          # 参赛者可见
            │   ├── train.csv                    # 训练数据
            │   └── sample_submission.csv        # 提交格式
            └── private/                         # 评分用
                └── answer.csv                   # 测试集答案
```

---

## 核心组件

### 1. 比赛注册目录 (`competitions/`)

DABench 风格的比赛元数据和处理逻辑：

#### `config.yaml` - 比赛配置
```yaml
id: custom-house-price-prediction
name: House Price Prediction Challenge
competition_type: kaggle
grader:
  name: rmse
  grade_fn: competitions.custom-house-price-prediction.grade:grade
preparer: competitions.custom-house-price-prediction.prepare:prepare
```

#### `description.md` - 任务说明
- 任务描述和目标
- 数据特征说明
- 提交格式要求
- 评分标准

#### `prepare.py` - 数据准备
```python
def prepare(raw: Path, public: Path, private: Path):
    """
    将原始数据分为：
    - public/: 训练数据 (80%)
    - private/: 测试答案 (20%)
    """
```

#### `grade.py` - 评分函数
```python
def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    """计算 RMSE 分数"""
    rmse = np.sqrt(np.mean((predicted - actual) ** 2))
    return rmse
```

### 2. 数据集目录 (`data/`)

模拟 DSFlow 的数据组织方式：

```
data/custom-house-price-prediction/
├── raw/                       # 原始数据（由 prepare_example_data.py 生成）
│   └── houses.csv
└── prepared/                  # 由 prepare.py 生成
    ├── public/                # Agent 可见的数据
    │   ├── train.csv          # 包含特征和标签
    │   └── sample_submission.csv  # 提交格式模板
    └── private/               # Agent 不可见（评分用）
        └── answer.csv         # 测试集真实答案
```

### 3. Benchmark 类 (`custom_benchmark.py`)

继承自 `BaseBenchmark` 的实现：

```python
class HousePriceBenchmark(BaseBenchmark):
    def _load_problems(self) -> List[Dict]:
        """加载任务列表"""

    def get_result_columns(self) -> List[str]:
        """定义结果 CSV 列"""

    async def evaluate_problem(self, problem, eval_fn) -> Tuple:
        """执行和评估单个任务"""
```

---

## 快速开始

### 步骤 1: 生成原始数据

```bash
cd examples/custom_benchmark
python prepare_example_data.py
```

**输出**: `data/custom-house-price-prediction/raw/houses.csv` (100 条记录)

### 步骤 2: 准备数据集

```bash
cd competitions/custom-house-price-prediction
python prepare.py
```

**输出**:
- `data/.../prepared/public/train.csv` (80 条)
- `data/.../prepared/public/sample_submission.csv`
- `data/.../prepared/private/answer.csv` (20 条)

### 步骤 3: 测试 Benchmark

```bash
cd examples/custom_benchmark
python custom_benchmark.py
```

**输出**: 使用模拟评估函数测试完整流程，生成随机预测并计算 RMSE。

### 一键运行（推荐）

```bash
bash run_example.sh
```

详细说明见 [QUICKSTART.md](QUICKSTART.md)

---

## 扩展指南

### 添加新任务

1. **创建比赛目录**:
   ```bash
   mkdir -p competitions/my-new-task
   mkdir -p data/my-new-task/raw
   ```

2. **编写核心文件**:
   - `config.yaml` - 配置任务元数据
   - `description.md` - 描述任务要求
   - `prepare.py` - 实现数据准备逻辑
   - `grade.py` - 实现评分逻辑

3. **更新 Benchmark 类**:
   ```python
   def _load_problems(self):
       return [
           {"task_id": "my-new-task", ...},
           # 添加更多任务
       ]
   ```

### 自定义评分

修改 `competitions/*/grade.py` 实现不同的评分指标：

```python
# 分类任务 - Accuracy
def grade(submission, answers):
    accuracy = (submission['predicted'] == answers['actual']).mean()
    return accuracy

# 排序任务 - NDCG
def grade(submission, answers):
    from sklearn.metrics import ndcg_score
    score = ndcg_score(answers, submission)
    return score
```

### 支持不同任务类型

在 `TaskDefinition` 中指定任务类型：

```python
# Kaggle 风格（文件输入输出）
task = TaskDefinition(
    task_id="task-001",
    task_type="kaggle",
    payload={
        "public_data_dir": "./data/public",
        "output_submission_path": "./output.csv"
    }
)

# QA 风格（文本问答）
task = TaskDefinition(
    task_id="qa-001",
    task_type="qa",
    payload={
        "question": "What is the capital of France?"
    }
)
```

---

## 集成到框架

### 方法 1: 注册到 `run_benchmark.py`

编辑 `run_benchmark.py`:

```python
# 导入自定义 Benchmark
from examples.custom_benchmark.custom_benchmark import HousePriceBenchmark

# 注册到 BENCHMARK_CLASSES
BENCHMARK_CLASSES = {
    "mle": MLEBenchmark,
    "dabench": MLEBenchmark,
    "house_price": HousePriceBenchmark,  # 添加这行
}
```

### 方法 2: 添加 CLI 参数（可选）

如果需要自定义参数：

```python
parser.add_argument(
    "--custom-data-dir",
    type=str,
    default=None,
    help="Path to custom benchmark data"
)

# 在 benchmark 初始化中使用
if args.benchmark == "house_price":
    benchmark_kwargs["data_dir"] = args.custom_data_dir
```

### 运行自定义 Benchmark

```bash
python run_benchmark.py \
  --workflow aide \
  --benchmark house_price \
  --log-path ./runs/house_price_results
```

---

## 参考实现

| Benchmark | 文件 | 任务类型 | 特点 |
|-----------|------|---------|------|
| **MLEBenchmark** | `dsat/benchmark/mle.py` | Kaggle 竞赛 | 生产级实现，支持多竞赛 |
| **DataSciBenchmark** | `dsat/benchmark/datasci.py` | 多步骤工作流 | 复杂数据科学流程 |
| **HousePriceBenchmark** | `custom_benchmark.py` | 回归任务 | 本示例，完整 DABench 风格 |

---

## 常见问题

### Q: 如何验证数据准备是否正确？

```bash
# 检查文件是否生成
ls -lh data/custom-house-price-prediction/prepared/public/
ls -lh data/custom-house-price-prediction/prepared/private/

# 查看数据统计
python -c "
import pandas as pd
train = pd.read_csv('data/custom-house-price-prediction/prepared/public/train.csv')
print(f'训练集: {len(train)} 行')
print(train.describe())
"
```

### Q: 如何调试评分函数？

```bash
cd competitions/custom-house-price-prediction
python grade.py  # 运行内置测试
```

### Q: 如何更改数据集大小？

编辑 `prepare_example_data.py`:
```python
df = generate_house_data(n_samples=500)  # 从 100 改为 500
```

---

## 下一步

- 📖 阅读 [QUICKSTART.md](QUICKSTART.md) 了解快速开始
- 🔧 查看 `competitions/*/` 下的文件了解详细实现
- 🚀 运行 `bash run_example.sh` 体验完整流程
- 📚 参考 `dsat/benchmark/mle.py` 学习生产级实现

---

**作者**: DS-Lighting 团队
**版本**: 1.0
**更新**: 2025-12
