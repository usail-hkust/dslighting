# ScienceBench Task 3

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Feature Engineering, Machine Learning
- Source: hackingmaterials/matminer_examples
- Output Type: Tabular

## Task

Train a random forest model with the given dataset of inorganic crystalline compounds to predict their bulk modulus (K_VRH).

## Dataset

## Submission Format

Submit `sample_submission.csv` with the same header and column order as the template. Ensure numeric columns retain their dtype and identifiers remain aligned.

## Evaluation

Submissions are accepted when the predictions achieve an RMSE ≤ 24.0 against the gold `K_VRH` values.
