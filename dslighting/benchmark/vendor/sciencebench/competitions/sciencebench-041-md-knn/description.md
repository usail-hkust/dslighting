# ScienceBench Task 41

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Machine Learning
- Source: anikaliu/CAMDA-DILI
- Output Type: Tabular

## Task

Train K-nearest neighbor (KNN) classifiers on the molecular descriptor dataset to predict DILI risk. Build models for the `MCNC`, `MCLCNC`, and `all` splits and write predictions to separate CSV files per split, with columns `standardised_smiles` and `label` (`DILI` or `NoDILI`).

## Dataset

The `dili_MD/` directory contains the descriptor features (`mol_descriptors_training.csv`), compound metadata (`standardized_compounds_excl_ambiguous_cluster.csv`), and `test.csv` for evaluation.

## Submission Format

Produce one CSV per split (`all`, `MCNC`, `MCLCNC`), aligned to the order of `test.csv` and including the predicted labels.

## Evaluation

Submissions are accepted when the mean F1 score across the three splits meets the 0.73 threshold from the reference evaluation script.
