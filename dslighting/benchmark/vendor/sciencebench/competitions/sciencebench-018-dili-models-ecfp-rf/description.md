# ScienceBench Task 18

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Machine Learning
- Source: anikaliu/CAMDA-DILI
- Output Type: Tabular

## Task

Train a classification model on the provided Drug-Induced Liver Injury (DILI) training data and generate labels for the held-out test compounds. Keep the original ordering of the test set when producing your predictions.

## Dataset

The `dili/` directory provides:

- `train.csv` – labeled compounds with cluster metadata.
- `test.csv` – held-out compounds to score.

## Evaluation

The grader compares your submitted labels against the reference file and reports the F1 score using `DILI` as the positive class. The SMILES order must match the reference exactly.
