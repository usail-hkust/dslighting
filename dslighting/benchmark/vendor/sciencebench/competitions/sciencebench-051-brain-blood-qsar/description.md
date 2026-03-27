# ScienceBench Task 51

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Feature Engineering, Deep Learning
- Source: deepchem/deepchem
- Output Type: Tabular

## Task

Train a blood–brain barrier permeability model using the provided logBB dataset. Generate predictions for the held-out test set and write the class labels (`DILI` concern vs no concern, encoded as `1` or `0`) to a CSV file.

## Dataset

[START Dataset Preview: brain-blood]
|-- logBB.sdf
|-- logBB_test.sdf
[END Dataset Preview]

## Submission Format

Save a CSV file with at least a `label` column containing the predicted class for each entry in `logBB_test.sdf`.

## Evaluation

The grader loads the submitted labels, compares them with the reference labels, and accepts the submission when the balanced accuracy is at least 0.70.
