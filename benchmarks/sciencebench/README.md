# ScienceBench for DeepModeling Framework

ScienceBench是DeepModeling框架集成的102个科学计算任务基准测试，源自ScienceAgent-bench。

## 目录结构

```
/path/to/DeepModeling/benchmarks/sciencebench/
├── competitions/              # 竞赛注册目录（registry）
│   ├── __init__.py
│   ├── utils.py
│   ├── sciencebench-001-clintox-nn/
│   │   ├── config.yaml        # 竞赛配置
│   │   ├── description.md     # 任务描述
│   │   ├── prepare.py         # 数据准备脚本
│   │   ├── grade.py           # 评分函数
│   │   ├── leaderboard.csv    # 排行榜
│   │   └── checksums.yaml     # 校验和
│   ├── sciencebench-002-mat-feature-select/
│   └── ...                    # 共102个竞赛

/path/to/ScienceAgent-bench/
└── competitions/              # 数据目录（data-dir）
    ├── sciencebench-001-clintox-nn/
    │   └── prepared/
    │       ├── public/        # 公开数据（训练集）
    │       └── private/       # 私有数据（测试集答案）
    ├── sciencebench-002-mat-feature-select/
    └── ...
```

## 任务分类

- **Computational Chemistry** (20任务): 计算化学
- **Geographical Information Science** (27任务): 地理信息科学
- **Bioinformatics** (27任务): 生物信息学
- **Psychology and Cognitive Science** (28任务): 心理学与认知科学

## 使用方法

### 1. 列出所有任务

```bash
python examples/scienceagentbench-to-mlebench/convert_scienceagent_to_mlebench.py --list
```

### 2. 转换特定任务

```bash
python examples/scienceagentbench-to-mlebench/convert_scienceagent_to_mlebench.py --instance-ids 1 2 3
```

### 3. 转换所有任务

```bash
python examples/scienceagentbench-to-mlebench/convert_scienceagent_to_mlebench.py --all
```

### 4. 运行基准测试

```bash
python main.py \
  --workflow scientific \
  --benchmark sciencebench \
  --data-dir "/path/to/ScienceAgent-bench/competitions" \
  --llm-model openai/deepseek-ai/DeepSeek-V3.1-Terminus \
  --task sciencebench-001-clintox-nn
```

## 配置格式

每个竞赛的`config.yaml`格式：

```yaml
id: sciencebench-001-clintox-nn
name: "ScienceBench - clintox_nn.py"
competition_type: code
awards_medals: false
prizes: null
description: benchmarks/sciencebench/competitions/sciencebench-001-clintox-nn/description.md

dataset:
  answers: sciencebench-001-clintox-nn/prepared/private/answer.csv
  sample_submission: sciencebench-001-clintox-nn/prepared/public/sample_submission.csv

grader:
  name: accuracy
  grade_fn: benchmarks.sciencebench.competitions.sciencebench-001-clintox-nn.grade:grade

preparer: benchmarks.sciencebench.competitions.sciencebench-001-clintox-nn.prepare:prepare
```

## 评估指标

- `accuracy`: 准确率（分类任务）
- `rmse`: 均方根误差（回归任务，返回负值）
- `visual_similarity`: 视觉相似度（可视化任务）
- `exact_match`: 精确匹配（特征选择等）

## 技术细节

### 导入路径处理

竞赛ID中包含连字符（如`sciencebench-001-clintox-nn`），这在Python模块名中是无效的。我们使用与MLE-Bench相同的解决方案：

1. 在`benchmarks.mlebench.utils.import_fn`中处理带连字符的模块导入
2. ScienceBenchmark使用该函数动态加载grade和prepare函数
3. 为竞赛目录创建假父模块，支持相对导入

### 与MLE-Bench的兼容性

ScienceBench复用了MLE-Bench的导入机制：
- 使用`benchmarks.mlebench.utils.import_fn`处理动态导入
- 竞赛配置格式类似
- 支持相同的评估指标

## 注意事项

1. **数据准备**: 首次运行任务前，需要准备数据（运行prepare.py）
2. **依赖包**: 某些任务需要特定的科学计算库（如deepchem, matminer, geopandas等）
3. **计算资源**: 部分任务（特别是深度学习相关）可能需要GPU

## 转换脚本

转换脚本位置：`examples/scienceagentbench-to-mlebench/convert_scienceagent_to_mlebench.py`

主要功能：
- 从ScienceAgent-bench元数据生成竞赛配置
- 推断评估指标
- 生成prepare.py和grade.py
- 自动清理任务描述（去除文件路径等具体信息）

## 已知问题

1. 某些任务的原始数据可能需要从ScienceAgent-bench手动获取
2. 图像相似度评估是占位实现，需要根据具体任务调整
3. 部分任务的评估指标可能需要手动优化

## 更新日志

- 2025-11-03: 初始版本，转换了全部102个任务
- 采用MLE-Bench兼容的导入机制
- 简化的registry结构，无需复杂的Registry类
