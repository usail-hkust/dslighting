# ScienceBench Task 101

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Deep Learning
- Source: ppdebreuck/modnet
- Output Type: CSV

## Task

Train a MODNet-style regressor on the provided experimental band-gap dataset. Use the supplied training split to fit the model and predict the experimental band gap (`gap_expt_eV`) for the held-out structures.

## Dataset

[START Dataset Preview: experimental_band_gap]
|-- matbench_expt_gap_train.pkl
|-- matbench_expt_gap_test.pkl
[END Dataset Preview]

## Submission Format
matching the provided sample submission. Predictions must be aligned to the test set order.

## Evaluation

The grader measures mean absolute error against the gold targets (pass if MAE < 0.6 eV).
