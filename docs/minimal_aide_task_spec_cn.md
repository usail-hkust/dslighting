# AIDE 任务最小结构规范

本文档用于统一纯数据合成项目中 Data Science Agent 任务的最小落地结构。目标不是覆盖所有历史 MLEBench 文件，而是定义一套“能让 `aide` 工作流加载、运行、评分”的最小契约。

适用范围：
- 表格类监督学习任务
- 通过注册目录 + 数据目录组织任务
- 以 `bike-sharing-demand` 为参考

## 1. 结论先行

对 `aide` 来说，一个最小可运行任务需要两部分：

1. 注册侧：告诉框架“这是什么任务、怎么评分、数据在哪里”
2. 数据侧：给 agent 可见的数据，以及评分时隐藏的数据

推荐统一采用下面这套结构：

```text
dslighting/
├── dslighting/benchmark/vendor/mlebench/competitions/<task_id>/
│   ├── config.yaml
│   ├── description.md
│   ├── prepare.py
│   ├── grade.py
│   └── leaderboard.csv
└── data/competitions/<task_id>/
    └── prepared/
        ├── public/
        │   ├── train.csv
        │   ├── test.csv
        │   └── sample_submission.csv
        └── private/
            └── answer.csv
```

如果你们要和现有 `bike-sharing-demand` 保持完全一致，也可以用：

```text
data/competitions/<task_id>/prepared/public/sampleSubmission.csv
data/competitions/<task_id>/prepared/private/test_answer.csv
```

文件名不是强约束，真正的约束来自 `config.yaml` 里填写的路径。

## 2. 注册侧最小要求

目录：

```text
dslighting/benchmark/vendor/mlebench/competitions/<task_id>/
```

### 2.1 必需文件

#### `config.yaml`

这是核心注册文件。最小建议如下：

```yaml
id: my-synthetic-task
name: My Synthetic Task
competition_type: simple
description: vendor/mlebench/competitions/my-synthetic-task/description.md

dataset:
  answers: my-synthetic-task/prepared/private/answer.csv
  sample_submission: my-synthetic-task/prepared/public/sample_submission.csv

grader:
  name: rmse
  grade_fn: file:vendor/mlebench/competitions/my-synthetic-task/grade.py:grade

preparer: file:vendor/mlebench/competitions/my-synthetic-task/prepare.py:prepare
```

最少要统一的字段含义：

- `id`: 任务唯一 ID，必须和目录名一致
- `name`: 人类可读名称
- `competition_type`: 推荐统一写 `simple`
- `description`: 指向任务说明文件
- `dataset.answers`: 隐藏答案文件
- `dataset.sample_submission`: 提交样例文件
- `grader.name`: 指标名，展示用途
- `grader.grade_fn`: 评分函数入口
- `preparer`: 数据准备函数入口

#### `description.md`

给 agent 的题面。最少应包含：

- 任务目标
- 输入数据说明
- 目标列说明
- 提交格式说明
- 评价指标说明

#### `prepare.py`

函数签名必须兼容当前框架：

```python
from pathlib import Path

def prepare(raw: Path, public: Path, private: Path):
    ...
```

对于“纯合成数据，且已经直接产出 prepared 数据”的场景，可以把它写成一个非常薄的函数，只负责：

- 把现成文件复制到 `public/` 和 `private/`
- 做基本校验

不建议省略这个文件，因为注册器在加载任务时会导入这个函数。

#### `grade.py`

标准 CSV 预测任务推荐统一成：

```python
import pandas as pd

def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    ...
```

要求：

- 输入是 agent 的提交表和私有答案表
- 返回单个 `float`
- 非法提交时建议抛 `InvalidSubmissionError`

#### `leaderboard.csv`

这个文件在打分汇总时会被读取，至少需要有一列：

```csv
score
0.42
0.51
0.63
```

最小可用就是只有 `score` 列，至少 1 行。  
为了避免 medal threshold 太失真，建议放 5 到 20 行参考分数。

### 2.2 可选但建议保留

- `checksums.yaml`
  - 如果要走官方 `prepare/verify` 流程，建议保留
  - 如果你们当前只做本地合成任务，不强依赖
- `report.md`
  - 说明性材料，不参与加载契约
- `raw/` 路径配置
  - 对纯合成 prepared 数据不是必须

## 3. 数据侧最小要求

目录：

```text
data/competitions/<task_id>/prepared/
```

### 3.1 必需目录

```text
data/competitions/<task_id>/
└── prepared/
    ├── public/
    └── private/
```

这两个目录都必须存在，而且不能是空目录。

### 3.2 `public/` 中最少需要什么

对标准监督学习任务，建议至少包含：

- `train.csv`
  - 训练数据
  - 包含特征列和目标列
- `test.csv`
  - 测试数据
  - 只包含特征列，不包含目标列
- `sample_submission.csv`
  - 告诉 agent 最终提交长什么样

这是最稳妥的一套，因为 AIDE 会把 `public/` 当作 agent 的工作数据目录。

### 3.3 `private/` 中最少需要什么

至少需要一个答案文件，对应 `config.yaml` 里的 `dataset.answers`：

- `answer.csv`
  - 一般包含主键列 + 标签列

### 3.4 数据层的最小语义约束

无论文件名怎么起，至少要满足：

- `sample_submission.csv` 和 `answer.csv` 行数一致
- `submission` 能和 `answer` 对齐
- `grade.py` 能明确知道如何对齐
- `test.csv` 的样本集合和 `answer.csv` 一一对应

对表格预测任务，推荐统一采用：

- 一列主键，如 `id` / `datetime`
- 一列预测目标，如 `target` / `count`

## 4. 以 bike-sharing-demand 对照

`bike-sharing-demand` 当前实际结构可以理解成下面这个映射：

### 注册侧

- `config.yaml`
  - 定义任务 ID、描述、答案路径、样例提交路径、评分函数、准备函数
- `prepare.py`
  - 把 raw 中的训练集、测试集、样例提交、答案分别拷到 `public/` 和 `private/`
- `grade.py`
  - 校验 `datetime,count` 两列，并计算 RMSLE

### 数据侧

`public/train.csv`
- 带标签训练集

`public/test.csv`
- 不带标签测试集

`public/sampleSubmission.csv`
- 提交模板，列为 `datetime,count`

`private/test_answer.csv`
- 隐藏答案，列也为 `datetime,count`

所以它的本质并不复杂，核心就是：

1. agent 看见 `train/test/sample_submission`
2. grader 看见 `submission/answer`
3. `grade.py` 定义二者如何比较

需要注意一件事：

- 当前 `bike-sharing-demand` 目录里存在一个历史不一致
- `config.yaml` 指向的是 `prepared/private/test_answer.csv`
- 但 `prepare.py` 里写出的却是 `private/test.csv`

这说明旧任务样例不能原样当模板复用。你们的新任务建议统一成单一命名，不要让 `config.yaml`、`prepare.py`、真实落盘文件三者出现分叉。

## 5. 纯合成任务的推荐模板

如果你们现在做的是“纯数据合成”，建议直接统一成下面这个模板，不要引入多余变体：

```text
dslighting/benchmark/vendor/mlebench/competitions/<task_id>/
├── config.yaml
├── description.md
├── prepare.py
├── grade.py
└── leaderboard.csv

data/competitions/<task_id>/
└── prepared/
    ├── public/
    │   ├── train.csv
    │   ├── test.csv
    │   └── sample_submission.csv
    └── private/
        └── answer.csv
```

这样做的好处：

- 目录稳定，团队成员不用猜文件放哪
- `aide`、task loader、grader 三层都能复用现有逻辑
- 以后要扩展 `validation` split 或别的 workflow 也容易

## 6. 团队协作时建议统一的约定

建议提前约定以下规范：

1. `task_id` 全局唯一，目录名和 `config.yaml:id` 完全一致
2. 公共文件名统一用 `train.csv`、`test.csv`、`sample_submission.csv`、`answer.csv`
3. 每个任务都必须有明确主键列
4. `grade.py` 里先做格式校验，再算指标
5. `description.md` 必须明确“预测哪一列”和“提交文件长什么样”

## 7. 最小可运行判断标准

如果一个任务满足下面几点，就可以认为它已经达到最小可运行：

1. `config.yaml` 能被 registry 正常加载
2. `public/` 和 `private/` 都存在且非空
3. `sample_submission` 和 `answers` 路径真实存在
4. `grade.py` 可以对一个合法 submission 返回 `float`
5. `leaderboard.csv` 存在且至少有 `score` 列

---

如果后面你们准备把这套规范正式沉淀成模板，我建议下一步直接补一个 `task_id` 脚手架生成器，自动产出这 5 个注册文件和 `prepared/public/private` 目录。
