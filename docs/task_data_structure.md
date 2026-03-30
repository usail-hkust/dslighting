# Minimal DSLighting Task Data Structure

This document describes the public, minimal task contract used by DSLighting for
AIDE-style execution and `DSBenchmark` evaluation.

It focuses on the MLE-style task layout shared across benchmark sources such as
MLE-Bench, DABench, DACode, MoSciBench, and ScienceBench:

- a registry side inside the package
- a data side outside the package
- a public/private split for execution vs. grading

The goal is not to document every historical task variant. The goal is to define
the smallest stable structure that lets DSLighting load, run, and grade a task.

## 1. High-Level Model

At a high level, a DSLighting task has two parts:

1. Registry metadata and executable hooks
2. Prepared task data

Recommended layout:

```text
dslighting/
├── dslighting/benchmark/vendor/<source_id>/competitions/<task_id>/
│   ├── config.yaml
│   ├── description.md
│   ├── prepare.py
│   ├── grade.py
│   └── leaderboard.csv
└── <data_root>/<task_id>/
    └── prepared/
        ├── public/
        │   ├── train.csv
        │   ├── test.csv
        │   └── sample_submission.csv
        └── private/
            └── answer.csv
```

Conceptually:

- the registry side tells DSLighting what the task is and how to score it
- the data side contains the files used during execution and grading
- the agent sees `prepared/public/`
- the grader sees `prepared/private/`

## 2. Where `data_dir` Points

For `DSBenchmark`, the runtime receives a benchmark-specific `data_dir`.

In most MLE-style sources, `data_dir` points to a directory that directly
contains task folders:

```text
<data_root>/
├── <task_id>/
├── <task_id>/
└── ...
```

For example:

- `DSBenchmark("dabench", data_dir="/path/to/dabench")`
- `DSBenchmark("dacode", data_dir="/path/to/dacode")`
- `DSBenchmark("sciencebench", data_dir="/path/to/scienceagentbench")`

Some public releases use an extra `competitions/` layer, such as MoSciBench:

```text
/path/to/moscibench/
├── competitions/
└── metadata/
```

In that case, `data_dir` should point to `competitions/`.

## 3. Minimal Registry Contract

Registry directory:

```text
dslighting/benchmark/vendor/<source_id>/competitions/<task_id>/
```

### Required files

#### `config.yaml`

This is the core task registration file.

Recommended minimal example:

```yaml
id: my-synthetic-task
name: My Synthetic Task
competition_type: simple
description: description.md

dataset:
  answers: my-synthetic-task/prepared/private/answer.csv
  sample_submission: my-synthetic-task/prepared/public/sample_submission.csv

grader:
  name: rmse
  grade_fn: file:grade.py:grade

preparer: file:prepare.py:prepare
```

Minimum field semantics:

- `id`: globally unique task ID; should match the directory name
- `name`: human-readable task name
- `competition_type`: usually `simple` for standard prediction tasks
- `description`: task statement shown to the agent/runtime
- `dataset.answers`: private answer file used by the grader
- `dataset.sample_submission`: public template for final output
- `grader.name`: metric name for display and reports
- `grader.grade_fn`: Python entrypoint for grading
- `preparer`: Python entrypoint for data preparation

#### `description.md`

This is the task statement. It should clearly describe:

- the task objective
- the input files
- the target column or output artifact
- the expected submission format
- the evaluation metric

#### `prepare.py`

Expected function signature:

```python
from pathlib import Path

def prepare(raw: Path, public: Path, private: Path):
    ...
```

For synthetic or already-prepared tasks, this can be a very thin function that:

- copies files into `public/` and `private/`
- performs basic validation

It is best to keep this file even for simple tasks, because the registry expects
the preparation hook to exist.

#### `grade.py`

For standard tabular prediction tasks, a common pattern is:

```python
import pandas as pd

def grade(submission: pd.DataFrame, answers: pd.DataFrame) -> float:
    ...
```

Requirements:

- input is the agent submission plus the private answers
- output is a single `float`
- invalid submissions should fail clearly, ideally via a structured exception

#### `leaderboard.csv`

This file is used for score summaries and benchmark reporting.

The minimal usable form is:

```csv
score
0.42
0.51
0.63
```

At minimum:

- it should exist
- it should contain a `score` column
- it should have at least one row

### Optional but useful files

- `checksums.yaml`
  - useful for verification and reproducibility
- `report.md`
  - useful for humans, not required by the runtime
- extra raw-data metadata
  - useful for preparation pipelines, not required for the minimal contract

## 4. Minimal Data Contract

Data directory:

```text
<data_root>/<task_id>/prepared/
```

### Required directories

```text
<data_root>/<task_id>/
└── prepared/
    ├── public/
    └── private/
```

Both directories should exist and should not be empty.

### What should be in `public/`

For a standard supervised tabular task, the safest default is:

- `train.csv`
- `test.csv`
- `sample_submission.csv`

This is the directory exposed to the agent during execution.

### What should be in `private/`

At minimum:

- `answer.csv`

This is the hidden grading target referenced by `dataset.answers` in
`config.yaml`.

### Data-level invariants

Regardless of filenames, the task should satisfy these rules:

- `sample_submission` and `answer` align row-wise or key-wise
- `test` and `answer` refer to the same evaluation instances
- `grade.py` defines the alignment rule unambiguously
- the submission template matches what the grader expects

For tabular prediction tasks, it is strongly recommended to use:

- one explicit key column, such as `id` or `datetime`
- one explicit prediction column, such as `target` or `count`

## 5. Reference Minimal Layout

Recommended stable template:

```text
dslighting/benchmark/vendor/<source_id>/competitions/<task_id>/
├── config.yaml
├── description.md
├── prepare.py
├── grade.py
└── leaderboard.csv

<data_root>/<task_id>/
└── prepared/
    ├── public/
    │   ├── train.csv
    │   ├── test.csv
    │   └── sample_submission.csv
    └── private/
        └── answer.csv
```

Why this layout works well:

- the directory structure is stable and easy to reason about
- `aide`, task loading, and grading can all reuse the same assumptions
- future extensions such as validation splits or alternate workflows stay easy

## 6. Historical Compatibility Notes

Older tasks may use names such as:

- `sampleSubmission.csv`
- `test_answer.csv`

These names are not inherently wrong. The authoritative contract is the path
declared in `config.yaml`.

For new public tasks, it is better to standardize on:

- `train.csv`
- `test.csv`
- `sample_submission.csv`
- `answer.csv`

This avoids drift between:

- `config.yaml`
- `prepare.py`
- actual files written to disk

## 7. Recommended Team Conventions

For collaborative task creation, it is useful to standardize the following:

1. `task_id` is globally unique and exactly matches `config.yaml:id`
2. canonical public filenames are reused across tasks whenever possible
3. every task has a clear primary key or alignment rule
4. `grade.py` validates submission format before computing the metric
5. `description.md` explicitly states the target column or required output file

## 8. Minimal Readiness Checklist

A task can be considered minimally runnable if all of the following are true:

1. `config.yaml` loads successfully through the registry
2. `prepared/public/` and `prepared/private/` both exist and are non-empty
3. `dataset.sample_submission` and `dataset.answers` resolve to real files
4. `grade.py` returns a `float` for a valid submission
5. `leaderboard.csv` exists and contains at least a `score` column

---

If you plan to turn this contract into a production task-creation workflow, the
next practical step is to add a scaffold generator that creates:

- the five registry files
- the `prepared/public/` and `prepared/private/` directories
- a starter `config.yaml`, `prepare.py`, and `grade.py`
