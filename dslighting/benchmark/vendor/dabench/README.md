# DABench Source Notes

This vendor package contains the `dslighting` registry for the DABench (InfiAgent-DABench) benchmark source.

---

## 🔥 News

- **2024-01-01**: DABench is now available in `dslighting` with 257 normalized data analysis tasks.
- **2024-01-01**: Supports MLEBench evaluation pipeline with automatic grading for closed-form questions.

---

## Upstream source

- Repository: <https://github.com/InfiAgent/InfiAgent-DABench>
- Paper: <https://arxiv.org/abs/2401.05507>

Paper title:

`InfiAgent-DABench: Evaluating Agents on Data Analysis Tasks`

---

## What is stored here

This directory stores the **task registry layer** used by `dslighting`, not the full benchmark payload itself.

- `benchmark.yaml`
  - source descriptor for the `dabench` benchmark source
- `competitions/`
  - normalized task registry entries (257 tasks)
  - each task contains config, description, grader, preparer, checksums, and leaderboard metadata
- `registry.py`
  - compatibility wrapper around the generic `MLEStyleRegistry`

---

## Introduction

InfiAgent-DABench is a project to build and evaluate agents for advanced data analysis. Agent evaluation has been an open and challenging problem. It formulates LLMs as agents via a REACT pipeline. InfiAgent supports LLMs including local models (e.g., Llama) and API call (e.g., GPT-4). In this repo, we also build an evaluation benchmark and leaderboard to evaluate data analysis agents.

We provide an automatic evaluation for closed-form questions. In closed-form evaluation, the model is required to generate the response in the specific way and we use the exact match to evaluate the performance. Considering that most models hardly follow the format requirements, we add a reformat step after the models respond with GPT-3.5 which formats the responses with the format requirements.

---

## Dataset

Our evaluation dataset includes a validation dataset and a test dataset. We only keep validation dataset for public.

The validation dataset comprises two .jsonl files, with each line representing a JSON-format dictionary containing the following keys. Additionally, a directory of CSV files for the associated questions is located under `data/`:

**Questions**: `data/da-dev-questions.jsonl`
- `id`: Unique identifier for each question.
- `question`: The description of the data analysis question.
- `concepts`: The concepts involved in the question.
- `constraints`: The constraints on the question that narrow down the solution into a closed-form.
- `format`: The format requirements for the output.
- `file_name`: The file name of the corresponding csv file.
- `level`: The difficulty level for each question.

**Labels**: `data/da-dev-labels.jsonl`
- `id`: Unique identifier for each question.
- `common_answers`: A list of labels in the format: `[[answer_name1, answer1],[answer_name2, answer2], ...]` which are corresponding to `"@answer_name[answer]"` in the format part of questions.

**Files**: `data/da-dev-tables`

---

## Data layout in dslighting

`dslighting` treats DABench as a registry/data split source:

- Registry:
  - this directory
  - `<registry>/dslighting/benchmark/vendor/dabench`
- Data:
  - expected outside the package tree
  - resolved through `DSLIGHTING_DABENCH_DATA` or the caller-provided data root

In the current local setup, the normalized DABench task data lives under a separate data tree (`<data>/dabench/`), while this vendor package only carries the registry definitions.

---

## Adaptation notes

The upstream DABench release and the local `dslighting` runtime do not share exactly the same task contract shape. This registry is a normalized adaptation for the `mle_task_contract/v1` runtime used by `dslighting`.

Notable local adaptations include:

- normalized task ids under the `dabench-*` namespace
- task-local `config.yaml`, `prepare.py`, and `grade.py` contracts
- MLEBench-format directory structure with `raw/`, `prepared/public/`, and `prepared/private/` subdirectories
- automatic answer format conversion from `common_answers` to `@key[value]` format
- removal of machine-specific hardcoded paths in `prepare.py`

---

## DA-Agent

We release weights of DA-Agent 7b, 13b and 34b at huggingface.

---

## Contact

If you have any questions, feedback, or would like to collaborate on this project, please feel free to reach out to us through huxueyu@zju.edu.cn. Your inquiries and suggestions are highly appreciated.

Thank you for your interest in our work!

---

## Citation

If you use this source, cite the original DABench paper:

```bibtex
@misc{hu2024infiagentdabench,
  title={InfiAgent-DABench: Evaluating Agents on Data Analysis Tasks},
  author={Xueyu Hu and Ziyu Zhao and Shuang Wei and Ziwei Chai and Qianli Ma and Guoyin Wang and Xuwu Wang and Jing Su and Jingjing Xu and Ming Zhu and Yao Cheng and Jianbo Yuan and Jiwei Li and Kun Kuang and Yang Yang and Hongxia Yang and Fei Wu},
  year={2024},
  eprint={2401.05507},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2401.05507},
}
```
