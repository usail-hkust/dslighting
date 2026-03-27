# ScienceBench Task 58

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: nriesterer/syllogistic-nvc
- Output Type: Tabular

## Task

Aggregate the participant-level responses to count how often each model–rule pairing appears. Save the summary as a CSV file using semicolon-delimited rows with the columns `Model`, `Rule`, and `Num persons`.

## Dataset

[START Dataset Preview: nvc]
|-- Ragni2016.csv
|-- accuracies_data_for_plot.csv
|-- ind_data_for_plot.csv
|-- valid_syllogisms.csv
[END Dataset Preview]

## Submission Format

Save predictions with semicolon-delimited columns `Model`, `Rule`, and `Num persons`. Provide one row per model–rule combination with the corresponding participant counts.

## Evaluation

The grader normalises both CSV files, sorts by `Model` and `Rule`, and requires an exact match with the reference counts.
