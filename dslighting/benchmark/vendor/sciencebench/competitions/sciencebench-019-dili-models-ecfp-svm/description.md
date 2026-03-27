# ScienceBench Task 19

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Machine Learning
- Source: anikaliu/CAMDA-DILI
- Output Type: Tabular

## Task

Train a support vector machine classifier on the provided Drug-Induced Liver Injury (DILI) training data and generate predictions for the held-out test compounds. Map the vDILIConcern labels to a binary outcome (`DILI` vs `NoDILI`) and keep the test set ordering intact when producing your outputs.

## Dataset

The `dili/` directory provides:

- `train.csv` – labeled compounds with cluster metadata.
- `test.csv` – held-out compounds to score.

## Evaluation

The grader compares your submitted labels against the reference file and reports the F1 score using `DILI` as the positive class. The SMILES order must match the reference exactly.
