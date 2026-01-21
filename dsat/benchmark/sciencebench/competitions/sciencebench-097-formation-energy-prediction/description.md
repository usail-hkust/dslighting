# ScienceBench Task 97

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Deep Learning
- Source: deepchem/deepchem
- Output Type: CSV (numeric)

## Task

Train a formation-energy predictor using the provided perovskite training molecules and output the predicted energies for the test set in the original order.

## Dataset

[START Dataset Preview: perovskite]
|-- perovskite_train.pkl
|-- perovskite_test.pkl
[END Dataset Preview]

## Submission Format

Submit a `.csv` file with a single `formation_energy` column containing one floating-point prediction per test example, aligned with the order of entries in `perovskite_test.pkl`.

## Evaluation

The grader computes the mean squared error against the gold targets (pass if MSE ≤ 0.1).
