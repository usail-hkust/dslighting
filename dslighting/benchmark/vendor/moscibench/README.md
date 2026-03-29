# MoSciBench Competitions

This directory hosts the competition definitions for the MoSciBench workflow. MoSciBench is the first benchmark focused on end-to-end multimodal scientific discovery with LLM agents, built from peer-reviewed studies across 6 scientific domains.

**Paper**: [Towards Multimodal Data-Driven Scientific Discovery Powered by LLM Agents](https://openreview.net/forum?id=) (ICLR 2025)

**Upstream repository**: https://github.com/usail-hkust/MoSciBench

## Benchmark Overview

- **88** benchmark tasks across **6** scientific domains
- **7** data modalities: timeseries, tabular, image, mass spectra, molecular structures, genotype matrix, text
- **5** discovery question types: Descriptive, Correlational, Causal Inference, Predictive, Pattern Discovery
- Each task requires cross-modal hypothesis verification — the agent generates executable code, runs it on raw data, and determines whether the hypothesis is supported

## Domain Summary

| Domain | Family | Tasks | Modalities |
|---|---|---|---|
| Earth Science | cyclone | 14 | timeseries, hdf (matrix), tabular |
| Biomedical Engineering | health_spa | 17 | timeseries (multi sensors) |
| Cheminformatics | massspecgym | 15 | mass spectra, molecular structures, tabular |
| Health Psychology | nurse_stress | 15 | timeseries (multi sensors), tabular |
| Population Genomics | pop_genetics | 13 | genotype matrix, tabular |
| Earth System Science | terra | 14 | image, tabular, timeseries |

## Adding a New Competition

To register an additional competition, add a new folder under `benchmark/vendor/moscibench/competitions/<competition-name>` and include the following files:

1. `config.yaml` – competition metadata (ID, task type, grader, dataset paths).
2. `description.md` – problem statement, dataset details, and submission format.
3. `prepare.py` – data preparation hook that materializes public/private artifacts from the raw data directory.
4. `grade.py` – scoring logic that consumes a submission and private ground-truth, returns a float score.

Place the actual dataset assets in the paired data directory at `data/moscibench/<competition-name>/prepared/`:

- `prepared/public/` – files exposed to the agent (inputs, sample submission).
- `prepared/private/` – ground-truth labels used exclusively for scoring.

Set the data root via environment variable:

```bash
export DSLIGHTING_MOSCIBENCH_DATA=/path/to/data/moscibench
```

## Available Competitions

| # | Competition | Domain | Grader |
|---|---|---|---|
| 1 | mosci-cyclone-1 | cyclone | structured_answer |
| 2 | mosci-cyclone-2 | cyclone | structured_answer |
| 3 | mosci-cyclone-3 | cyclone | structured_answer |
| 4 | mosci-cyclone-4 | cyclone | structured_answer |
| 5 | mosci-cyclone-5 | cyclone | structured_answer |
| 6 | mosci-cyclone-6 | cyclone | structured_answer |
| 7 | mosci-cyclone-7 | cyclone | structured_answer |
| 8 | mosci-cyclone-8 | cyclone | structured_answer |
| 9 | mosci-cyclone-9 | cyclone | structured_answer |
| 10 | mosci-cyclone-10 | cyclone | structured_answer |
| 11 | mosci-cyclone-11 | cyclone | structured_answer |
| 12 | mosci-cyclone-12 | cyclone | structured_answer |
| 13 | mosci-cyclone-13 | cyclone | structured_answer |
| 14 | mosci-cyclone-14 | cyclone | structured_answer |
| 15 | mosci-health_spa-1 | health_spa | structured_answer |
| 16 | mosci-health_spa-2 | health_spa | structured_answer |
| 17 | mosci-health_spa-3 | health_spa | structured_answer |
| 18 | mosci-health_spa-4 | health_spa | structured_answer |
| 19 | mosci-health_spa-5 | health_spa | structured_answer |
| 20 | mosci-health_spa-6 | health_spa | structured_answer |
| 21 | mosci-health_spa-7 | health_spa | structured_answer |
| 22 | mosci-health_spa-8 | health_spa | structured_answer |
| 23 | mosci-health_spa-9 | health_spa | structured_answer |
| 24 | mosci-health_spa-10 | health_spa | structured_answer |
| 25 | mosci-health_spa-11 | health_spa | structured_answer |
| 26 | mosci-health_spa-12 | health_spa | structured_answer |
| 27 | mosci-health_spa-13 | health_spa | structured_answer |
| 28 | mosci-health_spa-14 | health_spa | structured_answer |
| 29 | mosci-health_spa-15 | health_spa | structured_answer |
| 30 | mosci-health_spa-16 | health_spa | structured_answer |
| 31 | mosci-health_spa-17 | health_spa | structured_answer |
| 32 | mosci-massspecgym-1 | massspecgym | structured_answer |
| 33 | mosci-massspecgym-2 | massspecgym | structured_answer |
| 34 | mosci-massspecgym-3 | massspecgym | structured_answer |
| 35 | mosci-massspecgym-4 | massspecgym | structured_answer |
| 36 | mosci-massspecgym-5 | massspecgym | structured_answer |
| 37 | mosci-massspecgym-6 | massspecgym | structured_answer |
| 38 | mosci-massspecgym-7 | massspecgym | structured_answer |
| 39 | mosci-massspecgym-8 | massspecgym | structured_answer |
| 40 | mosci-massspecgym-9 | massspecgym | structured_answer |
| 41 | mosci-massspecgym-10 | massspecgym | structured_answer |
| 42 | mosci-massspecgym-11 | massspecgym | structured_answer |
| 43 | mosci-massspecgym-12 | massspecgym | structured_answer |
| 44 | mosci-massspecgym-13 | massspecgym | structured_answer |
| 45 | mosci-massspecgym-14 | massspecgym | structured_answer |
| 46 | mosci-massspecgym-15 | massspecgym | structured_answer |
| 47 | mosci-nurse_stress-1 | nurse_stress | structured_answer |
| 48 | mosci-nurse_stress-2 | nurse_stress | structured_answer |
| 49 | mosci-nurse_stress-3 | nurse_stress | structured_answer |
| 50 | mosci-nurse_stress-4 | nurse_stress | structured_answer |
| 51 | mosci-nurse_stress-5 | nurse_stress | structured_answer |
| 52 | mosci-nurse_stress-6 | nurse_stress | structured_answer |
| 53 | mosci-nurse_stress-7 | nurse_stress | structured_answer |
| 54 | mosci-nurse_stress-8 | nurse_stress | structured_answer |
| 55 | mosci-nurse_stress-9 | nurse_stress | structured_answer |
| 56 | mosci-nurse_stress-10 | nurse_stress | structured_answer |
| 57 | mosci-nurse_stress-11 | nurse_stress | structured_answer |
| 58 | mosci-nurse_stress-12 | nurse_stress | structured_answer |
| 59 | mosci-nurse_stress-13 | nurse_stress | structured_answer |
| 60 | mosci-nurse_stress-14 | nurse_stress | structured_answer |
| 61 | mosci-nurse_stress-15 | nurse_stress | structured_answer |
| 62 | mosci-pop_genetics-1 | pop_genetics | structured_answer |
| 63 | mosci-pop_genetics-2 | pop_genetics | structured_answer |
| 64 | mosci-pop_genetics-3 | pop_genetics | structured_answer |
| 65 | mosci-pop_genetics-4 | pop_genetics | structured_answer |
| 66 | mosci-pop_genetics-5 | pop_genetics | structured_answer |
| 67 | mosci-pop_genetics-6 | pop_genetics | structured_answer |
| 68 | mosci-pop_genetics-7 | pop_genetics | structured_answer |
| 69 | mosci-pop_genetics-8 | pop_genetics | structured_answer |
| 70 | mosci-pop_genetics-9 | pop_genetics | structured_answer |
| 71 | mosci-pop_genetics-10 | pop_genetics | structured_answer |
| 72 | mosci-pop_genetics-11 | pop_genetics | structured_answer |
| 73 | mosci-pop_genetics-12 | pop_genetics | structured_answer |
| 74 | mosci-pop_genetics-13 | pop_genetics | structured_answer |
| 75 | mosci-terra-1 | terra | structured_answer |
| 76 | mosci-terra-2 | terra | structured_answer |
| 77 | mosci-terra-3 | terra | structured_answer |
| 78 | mosci-terra-4 | terra | structured_answer |
| 79 | mosci-terra-5 | terra | structured_answer |
| 80 | mosci-terra-6 | terra | structured_answer |
| 81 | mosci-terra-7 | terra | structured_answer |
| 82 | mosci-terra-8 | terra | structured_answer |
| 83 | mosci-terra-9 | terra | structured_answer |
| 84 | mosci-terra-10 | terra | structured_answer |
| 85 | mosci-terra-11 | terra | structured_answer |
| 86 | mosci-terra-12 | terra | structured_answer |
| 87 | mosci-terra-13 | terra | structured_answer |
| 88 | mosci-terra-14 | terra | structured_answer |

**Total: 88 tasks across 6 domains**

## Citation

```bibtex
@inproceedings{liutowards,
  title     = {Towards Multimodal Data-Driven Scientific Discovery Powered by LLM Agents},
  author    = {Liu, Fan and Zeng, Xiaozhao and Liu, Hao},
  booktitle = {The Fourteenth International Conference on Learning Representations},
  year      = {2025}
}
```
