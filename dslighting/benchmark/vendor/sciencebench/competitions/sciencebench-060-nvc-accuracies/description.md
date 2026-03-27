# ScienceBench Task 60

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: nriesterer/syllogistic-nvc
- Output Type: Tabular

## Task

Evaluate the syllogistic reasoning accuracies produced by multiple models and compare them against the most frequent answers. Export the full comparison as a CSV file.

## Dataset

[START Dataset Preview: nvc]
|-- Ragni2016.csv
|-- accuracies_data_for_plot.csv
|-- ind_data_for_plot.csv
|-- valid_syllogisms.csv
[END Dataset Preview]

## Submission Format

Save predictions with the same columns and ordering as the template (`model`, `nvc`, `task`, `prediction`, `plain_prediction`, `truth`, `improvement`, `hit_model`, `hit_nvc`). Preserve string formatting and numeric precision.

## Evaluation

The grader sorts both CSV files lexicographically across all columns and requires an exact match with the reference data.
