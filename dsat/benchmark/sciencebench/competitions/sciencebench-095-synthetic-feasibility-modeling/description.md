# ScienceBench Task 95

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Feature Engineering, Deep Learning
- Source: deepchem/deepchem
- Output Type: NumPy array

## Task

Train a synthetic feasibility surrogate model using the provided Tox21 train/test molecule sets. Use the specified featurisation pipeline (ECFP radius 2, 512 bits) to predict the synthetic complexity scores for the test molecules and save the resulting NumPy array.

## Dataset

[START Dataset Preview: tox21]
|-- train_mols.pkl
|-- test_mols.pkl
[END Dataset Preview]

## Submission Format

Submit a `.npy` file containing a 1D NumPy array of predicted scores. The array must align with the order of molecules in `test_mols.pkl`.

## Evaluation

The grader computes the mean squared error against the gold scores (pass if MSE ≤ 0.4).
