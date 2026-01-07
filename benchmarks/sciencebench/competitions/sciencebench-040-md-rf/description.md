# ScienceBench Task 40

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Machine Learning
- Source: anikaliu/CAMDA-DILI
- Output Type: Tabular

## Task

Use molecular descriptors to train a model that predicts DILI risk and generate predictions for the evaluation set.

Write a single submission CSV that matches the provided `sample_submission.csv` format exactly, with columns:

- `test_data_id`
- `label` (`DILI` or `NoDILI`)

## Dataset

The `dili_MD/` directory contains:

- `mol_descriptors_training.csv` – descriptor features with labels and split annotations.
- `standardized_compounds_excl_ambiguous_cluster.csv` – metadata for compounds.
- `test.csv` – descriptor features for the evaluation set.

## Submission Format

Submit a single CSV matching `sample_submission.csv` (same header and row order).

## Evaluation

The grader compares your submitted `label` values against the reference and reports the F1 score using `DILI` as the positive class.
