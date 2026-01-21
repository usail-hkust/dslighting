# ScienceBench Task 13

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Deep Learning
- Source: kexinhuang12345/DeepPurpose
- Output Type: Tabular

## Task

Train an HIV activity prediction model using the provided training splits. Evaluate the trained model on `HIV_test.csv`, producing a ranked inference table. Save the results to the required output CSV, preserving the original column names (e.g., `smiles`, `HIV_active`).

## Dataset

The `hiv/` directory includes the assay data:

- `HIV_train.csv` – labeled training samples.
- `HIV_dev.csv` – development split.
- `HIV_test.csv` – held-out test compounds to score.
- `HIV_README` – metadata describing the dataset.

## Submission Format

Create submission matching `HIV_test.csv`. Include every SMILES from the test split and supply your predicted `HIV_active` values. Preserve the `activity` column in the same position even if you do not modify it.

## Evaluation

Submissions are accepted when the SMILES ordering matches the gold file and the F1 score on `HIV_active` meets or exceeds the 0.43 threshold used in the reference evaluation.
