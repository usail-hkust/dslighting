# DSLighting Benchmark 系统

## 概述

全新的 DSLighting Benchmark 系统提供了**轻量级但功能完整**的批量评估能力。

### 核心特性

✅ **轻量化**: 不依赖完整的 MLE-Bench 框架
✅ **配置驱动**: 通过 `config.yaml` 定义批量任务
✅ **多重继承**: 可以继承开源 Benchmark 的能力
✅ **统一接口**: 所有 Benchmark 使用相同的 API
✅ **统计分析**: 自动计算平均分、中位数、成本等

---

## 架构设计

### 继承关系

```
BaseBenchmark (DSLighting 基础能力)
    ├── 统一接口 (run_evaluation, get_statistics)
    ├── 统计分析 (平均分、成本等)
    └── 配置驱动 (config.yaml)
         ↑
         │ 多重继承
         │
MLELiteBenchmark ──────→ MLEBenchmark (开源能力)
    ├── 任务加载         ├── Registry 查找
    ├── 评分逻辑         ├── grade_csv
    └── 数据解析         └── Competition 管理
```

### 核心类

| 类 | 作用 | 继承 |
|---|---|---|
| `BaseBenchmark` | 基础 Benchmark | 无 |
| `MLELiteBenchmark` | MLE-Bench Lite | BaseBenchmark + MLEBenchmark |
| `CustomBenchmark` | 完全自定义 | BaseBenchmark |
| `BenchmarkFactory` | 工厂类 | 无 |

---

## 使用方式

### 1. MLELiteBenchmark（推荐）

**继承 MLE-Bench + DSLighting 双方能力**

```python
from dslighting.benchmark import MLELiteBenchmark

# 使用默认精选任务（10个核心竞赛）
benchmark = MLELiteBenchmark()

# 自定义任务列表
benchmark = MLELiteBenchmark(
    competitions=["bike-sharing-demand", "titanic", "house-prices"]
)

# 创建评估函数
async def eval_fn(task):
    agent = Agent()
    result = agent.run(task_id=task.task_id)
    return {
        "score": result.score,
        "cost": result.cost,
        "duration": result.duration,
    }

# 批量评估
results = await benchmark.run_evaluation(eval_fn, model_name="gpt-4")

# 统计分析
stats = benchmark.get_statistics()
print(f"平均分数: {stats['avg_score']}")
print(f"成功率: {stats['success_rate']}")
```

### 2. CustomBenchmark（轻量）

**完全使用 DSLighting 能力，不依赖开源框架**

```python
from dslighting.benchmark import CustomBenchmark
from dsat.models.task import TaskDefinition

# 创建任务列表
tasks = [
    TaskDefinition(
        task_id="my-task",
        task_type="kaggle",
        payload={"description": "..."}
    ),
]

# 创建 Benchmark
benchmark = CustomBenchmark("my-benchmark", tasks)

# 运行评估
results = await benchmark.run_evaluation(eval_fn)
```

### 3. BenchmarkFactory（配置驱动）

**从 config.yaml 加载批量任务**

```python
from dslighting.benchmark import BenchmarkFactory
from pathlib import Path

# 创建工厂
factory = BenchmarkFactory.from_config_file(
    config_path=Path("config.yaml"),
    registry_dir=Path("dslighting/registry"),
    data_dir=Path("data/competitions"),
)

# 列出可用的 Benchmark
benchmarks = factory.list_benchmarks()
print(f"可用 Benchmark: {benchmarks}")

# 创建 Benchmark
benchmark = factory.create("mle-lite")

# 运行评估
results = await benchmark.run_evaluation(eval_fn)
```

---

## 配置文件

### config.yaml 格式

```yaml
# ============================================================================
# DSLighting Benchmark 配置
# ============================================================================
benchmarks:
  # MLE-Bench Lite - 精选核心竞赛
  mle-lite:
    type: "mle-lite"
    description: "MLE-Bench Lite - 10个精选核心竞赛"
    competitions:
      - bike-sharing-demand
      - titanic
      - house-prices
      - new-york-city-taxi-fare-prediction
      - tabular-playground-series-dec-2021
      - histopathologic-cancer-detection
      - aptos2019-blindness-detection
      - spooky-author-identification
      - us-patent-phrase-to-phrase-matching
      - google-quest-challenge

  # 自定义 Benchmark（轻量级）
  my-custom:
    type: "custom"
    description: "自定义任务列表"
    tasks:
      - task_id: "bike-sharing-demand"
      - task_id: "titanic"

# ============================================================================
# MLE-Bench 竞赛配置（向后兼容）
# ============================================================================
competitions:
  - bike-sharing-demand
  - titanic
  # ...更多竞赛
```

---

## 统计分析

Benchmark 自动计算以下统计信息：

```python
stats = benchmark.get_statistics()

# 任务统计
stats["total_tasks"]           # 总任务数
stats["successful_tasks"]      # 成功任务数
stats["failed_tasks"]          # 失败任务数
stats["success_rate"]          # 成功率

# 分数统计
stats["avg_score"]             # 平均分数
stats["median_score"]          # 中位数分数
stats["std_score"]             # 标准差
stats["min_score"]             # 最低分
stats["max_score"]             # 最高分

# 成本统计
stats["avg_cost"]              # 平均成本
stats["total_cost"]            # 总成本

# 时长统计
stats["avg_duration"]          # 平均时长
stats["total_duration"]        # 总时长
```

---

## 文件结构

```
dslighting/benchmark/
├── __init__.py           # 导出所有 Benchmark 类
├── base.py               # BaseBenchmark 基类
├── factory.py            # BenchmarkFactory 工厂类
├── mle_lite.py           # MLELiteBenchmark
└── custom.py             # CustomBenchmark

examples/benchmark/
└── example_benchmark_usage.py  # 使用示例

tests/
└── test_benchmark.py     # 单元测试
```

---

## 与 MLEBenchmark 的对比

| 特性 | MLEBenchmark | MLELiteBenchmark |
|---|---|---|
| **依赖** | 完整的 MLE-Bench 框架 | 轻量化，可选 MLE-Bench |
| **任务加载** | 从 jsonl 文件 | 从配置或默认列表 |
| **接口** | MLE-Bench 原生接口 | DSLighting 统一接口 |
| **统计分析** | MLE-Bench 格式 | DSLighting 格式 |
| **配置驱动** | ❌ | ✅ 支持 config.yaml |
| **使用场景** | 完整的学术评估 | 快速原型测试 |

---

## 未来扩展

### 计划中的 Benchmark

1. **DABenchmark**: 数据分析 Benchmark
   ```python
   from dslighting.benchmark import DABenchmark
   benchmark = DABenchmark()
   ```

2. **ScienceBenchLite**: 科学推理 Benchmark 精简版
   ```python
   from dslighting.benchmark import ScienceBenchLite
   benchmark = ScienceBenchLite()
   ```

3. **自定义 Benchmark**: 用户可以轻松创建
   ```python
   class MyBenchmark(BaseBenchmark):
       def __init__(self):
           tasks = self._load_my_tasks()
           super().__init__("my-bench", tasks)
   ```

---

## 常见问题

### Q1: MLELiteBenchmark 和 MLEBenchmark 有什么区别？

**A**:
- **MLEBenchmark**: 完整的 MLE-Bench 框架，适合学术评估
- **MLELiteBenchmark**: 轻量化版本，继承 MLE-Bench 核心能力 + DSLighting 接口

### Q2: 如何选择使用哪个 Benchmark？

**A**:
- **快速测试**: 使用 `MLELiteBenchmark()`
- **自定义任务**: 使用 `CustomBenchmark`
- **配置驱动**: 使用 `BenchmarkFactory`
- **完整评估**: 使用 `MLEBenchmark` (DSAT)

### Q3: 可以混合使用不同来源的任务吗？

**A**: 可以！
```python
# 混合 MLE-Bench + 自定义任务
benchmark = MLELiteBenchmark(
    competitions=[
        "bike-sharing-demand",  # MLE-Bench
        "my-custom-task",        # 自定义
    ]
)
```

### Q4: 如何添加新的 Benchmark 类型？

**A**: 继承 `BaseBenchmark`:
```python
class MyBenchmark(BaseBenchmark):
    def __init__(self, name, tasks):
        super().__init__(name, tasks)

    # 可以添加自定义方法
    def custom_method(self):
        pass
```

---

## 总结

新的 DSLighting Benchmark 系统提供了：

✅ **轻量化**: 不需要完整的 MLE-Bench 框架
✅ **灵活性**: 支持配置驱动和完全自定义
✅ **扩展性**: 可以继承开源 Benchmark 的能力
✅ **统一性**: 所有 Benchmark 使用相同的 API
✅ **完整性**: 批量评估、统计分析、结果保存

开始使用：
```bash
# 运行示例
python examples/benchmark/example_benchmark_usage.py

# 运行测试
pytest tests/test_benchmark.py
```
