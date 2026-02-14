# ScienceBench Task 51

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Feature Engineering, Machine Learning
- Source: deepchem/deepchem (logBB / brain-blood)
- Output Type: Tabular

## Task

Train a blood–brain barrier permeability classifier using the provided logBB dataset.
Generate predictions for the held-out test set and write the class labels (`0/1`).

## Dataset

[START Dataset Preview: brain-blood]
|-- logBB.sdf
|-- logBB_test.sdf
[END Dataset Preview]

## Submission Format

Matching the provided `sample_submission.csv` format, with columns:

- `MolID` (e.g. `MolID_1`, taken from the first line of each record in `logBB_test.sdf`)
- `label` (predicted class `0/1`)

## Evaluation

The grader aligns rows by `MolID` and reports the balanced accuracy between predicted and reference labels.
