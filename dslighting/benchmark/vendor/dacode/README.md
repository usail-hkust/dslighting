# DACode Source Notes

This vendor package contains the `dslighting` registry for the DACode benchmark source.

## Upstream source

- Repository: <https://github.com/yiyihum/da-code>
- Paper: <https://arxiv.org/abs/2410.07331>

Paper title:

`DA-Code: Agent Data Science Code Generation Benchmark for Large Language Models`

## What is stored here

This directory stores the **task registry layer** used by `dslighting`, not the full benchmark payload itself.

- `benchmark.yaml`
  - source descriptor for the `dacode` benchmark source
- `competitions/`
  - normalized task registry entries
  - each task contains config, description, grader, preparer, checksums, and leaderboard metadata
- `registry.py`
  - compatibility wrapper around the generic `MLEStyleRegistry`

## Data layout in dslighting

`dslighting` treats DACode as a registry/data split source:

- Registry:
  - this directory
  - `/Users/liufan/projects/share/dslighting/dslighting/benchmark/vendor/dacode`
- Data:
  - expected outside the package tree
  - resolved through `DSLIGHTING_DACODE_DATA` or the caller-provided data root

In the current local setup, the normalized DACode task data lives under a separate data tree, while this vendor package only carries the registry definitions.

## Adaptation notes

The upstream DA-Code release and the local `dslighting` runtime do not share exactly the same task contract shape. This registry is a normalized adaptation for the `mle_task_contract/v1` runtime used by `dslighting`.

Notable local adaptations include:

- normalized task ids under the `dacode-*` namespace
- task-local `config.yaml`, `prepare.py`, and `grade.py` contracts
- artifact-oriented grading for single-file and multi-file submissions
- removal of machine-specific hardcoded paths in `prepare.py`
- compatibility fixes for JSON, DB, ML, and plot task variants

## Citation

If you use this source, cite the original DA-Code paper:

```bibtex
@misc{huang2024dacodeagentdatascience,
  title={DA-Code: Agent Data Science Code Generation Benchmark for Large Language Models},
  author={Yiming Huang and Jianwen Luo and Yan Yu and Yitong Zhang and Fangyu Lei and Yifan Wei and Shizhu He and Lifu Huang and Xiao Liu and Jun Zhao and Kang Liu},
  year={2024},
  eprint={2410.07331},
  archivePrefix={arXiv},
  primaryClass={cs.CL},
  url={https://arxiv.org/abs/2410.07331},
}
```
