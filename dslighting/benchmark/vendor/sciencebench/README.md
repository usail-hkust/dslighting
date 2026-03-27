# ScienceAgentBench Competitions

This directory hosts the competition definitions for the ScienceAgentBench workflow. ScienceAgentBench is a benchmark for evaluating language agents on data-driven scientific discovery tasks, sourced from peer-reviewed publications across four scientific disciplines.

**Paper**: [ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery](https://arxiv.org/abs/2410.05080) (ICLR 2025)

**Upstream repository**: https://github.com/OSU-NLP-Group/ScienceAgentBench

## Benchmark Overview

- **102** benchmark tasks extracted from **44** peer-reviewed papers
- **4** scientific disciplines: Bioinformatics, Chemoinformatics, Geoscience, Cognitive Neuroscience
- **9** subject matter experts validated all task instances
- Each task is a self-contained Python program generation problem evaluated on code execution results

## Adding a New Competition

To register an additional competition, add a new folder under `benchmark/vendor/sciencebench/competitions/<competition-name>` and include the following files:

1. `config.yaml` – top-level competition metadata (ID, task type, grader, dataset paths).
2. `description.md` – human-readable overview: problem statement, dataset details, and submission format.
3. `prepare.py` – data preparation hook that downloads/loads the raw data and materializes the prepared artifacts into the public/private directories defined in `config.yaml`.
4. `grade.py` – scoring logic that consumes a submission and the private ground-truth labels, then returns the configured metric.
5. `checksums.yaml` – SHA256 hashes for every artifact emitted by `prepare.py` to guard against accidental drift.
6. `leaderboard.csv` – optional sample leaderboard with historical submissions or reference baselines.

Place the actual dataset assets inside the paired data directory at `data/competitions/<competition-name>`, following the public/private split:

- `prepared/public/` – files exposed to the agent (inputs, sample submissions).
- `prepared/private/` – ground-truth labels used exclusively for scoring.

## Supported Disciplines

- **Bioinformatics** – molecular biology, genomics, protein modeling
- **Chemoinformatics** – drug property prediction, molecular modeling, toxicity
- **Geoscience** – materials science, earth observation, environmental modeling
- **Cognitive Neuroscience** – brain-behavior modeling, neural data analysis

## Available Competitions

| # | Competition | Discipline | Task Type | Metric |
|---|---|---|---|---|
| 001 | clintox-nn | Chemoinformatics | Classification | ROC-AUC |
| 002 | mat-feature-select | Materials Science | Feature Selection | Exact Match |
| 003 | predict-bulk-modulus | Materials Science | Regression | RMSE |
| 004 | elk-new | Geoscience | Visualization | Pixel Similarity |
| 005 | dkpes-model-development-1 | Chemoinformatics | Classification | Accuracy |
| 006-008 | dkpes-visualization-* | Chemoinformatics | Visualization | Pixel Similarity |
| 009 | factors-correlations | Geoscience | Visualization | Pixel Similarity |
| 010 | toronto-new | Geoscience | Visualization | Pixel Similarity |
| 011 | bbbc002-cell-count | Bioinformatics | Regression | MAE |
| 012 | davis-dti | Chemoinformatics | Ranking | List Match |
| 013 | drug-property-model | Chemoinformatics | Classification | F1 |
| 014 | flooding-gpd | Geoscience | Visualization | Pixel Similarity |
| 015 | aai | Bioinformatics | Classification | ROC-AUC |
| 016 | compound-filter | Chemoinformatics | Classification | Overlap |
| 017 | drugex-vis | Chemoinformatics | Visualization | Pixel Similarity |
| 018 | dili-models-ecfp-rf | Chemoinformatics | Classification | F1 |
| 019 | dili-models-ecfp-svm | Chemoinformatics | Classification | F1 |
| 020 | tdc-visualization | Chemoinformatics | Visualization | Pixel Similarity |
| 021 | deforestation | Geoscience | Regression | Relative Error |
| 022 | papyrus-filtering | Bioinformatics | Classification | Exact Match |
| 023 | deforestation-predict | Geoscience | Visualization | Pixel Similarity |
| 024-025 | ecg-processing-vis* | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 026 | ligand-fingerprint | Chemoinformatics | Classification | Accuracy |
| 027 | generate-plot-similarity | Chemoinformatics | Visualization | Pixel Similarity |
| 028 | charge-density-difference | Materials Science | Visualization | Pixel Similarity |
| 029 | bio-eventrelated-analyze | Cognitive Neuroscience | Regression | Tolerance |
| 030-031 | plot-phonon-* | Materials Science | Visualization | Pixel Similarity |
| 032 | coral-sponge | Bioinformatics | Visualization | Pixel Similarity |
| 033 | transit-access | Geoscience | Visualization | Pixel Similarity |
| 034 | hrv-analyze | Cognitive Neuroscience | Regression | Column Sum |
| 035 | rrv-analyze | Cognitive Neuroscience | Regression | Column Sum |
| 036 | eeg-processing-vis1 | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 037 | cft | Cognitive Neuroscience | Regression | Tolerance |
| 038 | fingerprint-similarity-vis | Chemoinformatics | Visualization | Pixel Similarity |
| 039 | protein-protein-fingerprint-similarity-vis | Chemoinformatics | Visualization | Pixel Similarity |
| 040 | md-rf | Chemoinformatics | Classification | F1 |
| 041 | md-knn | Chemoinformatics | Classification | F1 |
| 042 | edr-analyze | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 043 | eog-analyze | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 044 | imu | Cognitive Neuroscience | Regression | Tolerance |
| 045 | questionnaire | Cognitive Neuroscience | Regression | Tolerance |
| 046-050 | mountainlion*/sst*/eof-* | Geoscience | Visualization | Pixel Similarity |
| 051 | brain-blood-qsar | Chemoinformatics | Classification | Balanced Accuracy |
| 052 | aquatic-toxicity-qsar-vis | Chemoinformatics | Visualization | Pixel Similarity |
| 053-054 | mountainlion* | Geoscience | Visualization | Pixel Similarity |
| 055-056 | plot-ocean*/plot-temperature* | Geoscience | Visualization | Pixel Similarity |
| 057-062 | nvc-* | Cognitive Neuroscience | Visualization/Classification | Various |
| 063 | bio-interval-analyze | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 064-065 | plotting-* | Geoscience | Visualization | Pixel Similarity |
| 066-068 | cogsci-pattern-* | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 069 | single-cell-analysis-pca | Bioinformatics | Visualization | Pixel Similarity |
| 070 | single-cell-analysis-de | Bioinformatics | Visualization | Pixel Similarity |
| 071 | train-thingseeg2-linear | Cognitive Neuroscience | Regression | Spearman r |
| 072 | train-thingseeg2 | Cognitive Neuroscience | Regression | Spearman r |
| 073 | eeg2eeg-vis | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 074 | plotting-glacier-* | Geoscience | Visualization | Pixel Similarity |
| 075 | topic-modeling-lda | Bioinformatics | Visualization | Pixel Similarity |
| 076 | mineral-prospectivity-pred | Geoscience | Visualization | Pixel Similarity |
| 077 | waterquality | Geoscience | Visualization | Pixel Similarity |
| 078 | protein-stability | Bioinformatics | Regression | MAE |
| 079-082 | violin/genes-*/umap/dendrogram | Bioinformatics | Visualization | Pixel Similarity |
| 083 | urbanheat | Geoscience | Visualization | Pixel Similarity |
| 084 | burnscar | Geoscience | Visualization | Pixel Similarity |
| 085 | saliva | Cognitive Neuroscience | Regression | Tolerance |
| 086 | plot-tec | Geoscience | Visualization | Pixel Similarity |
| 087 | polynomial-fit | Physics | Regression | Exact Match |
| 088 | plot-collisions-map | Geoscience | Visualization | Pixel Similarity |
| 089 | plot-trees-count | Geoscience | Visualization | Pixel Similarity |
| 090 | run-jnmf | Cognitive Neuroscience | Matrix Factorization | Reconstruction Error |
| 091 | jnmf-plot-patterns | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 092 | h-importances | Cognitive Neuroscience | Regression | Tolerance |
| 093 | plot-h-distribution | Cognitive Neuroscience | Visualization | Pixel Similarity |
| 094 | polyverse-visualize-molecules | Chemoinformatics | Visualization | Pixel Similarity |
| 095 | synthetic-feasibility-modeling | Chemoinformatics | Regression | MSE |
| 096 | scatter | Bioinformatics | Visualization | Pixel Similarity |
| 097 | formation-energy-prediction | Materials Science | Regression | MSE |
| 098 | 3k | Bioinformatics | Visualization | Pixel Similarity |
| 099-100 | spatial* | Bioinformatics | Visualization | Pixel Similarity |
| 101 | experimental-band-gap-prediction | Materials Science | Regression | MAE |
| 102 | refractive-index-prediction | Materials Science | Regression | MAE |

**Total: 102 tasks across 4 disciplines**

## Citation

```bibtex
@inproceedings{chen2025scienceagentbench,
  title     = {ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery},
  author    = {Ziru Chen and Shijie Chen and Yuting Ning and others},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  url       = {https://arxiv.org/abs/2410.05080}
}
```
