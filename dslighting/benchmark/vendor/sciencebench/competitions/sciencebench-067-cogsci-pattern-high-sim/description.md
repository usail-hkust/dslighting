# ScienceBench Task 67

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: brand-d/cogsci-jnmf
- Output Type: Tabular

## Task

Compute similarity scores between cognitive models and the high-similarity personality patterns. Save the results as a CSV file with columns `model`, `conscientiousness`, and `openness`.

## Dataset

[START Dataset Preview: CogSci_pattern_high_sim_data]
|-- Atmosphere.csv
|-- Conversion.csv
|-- PHM.csv
|-- fit_result_conscientiousness_W_high.npy
[END Dataset Preview]

## Submission Format

Save predictions with columns `model`, `conscientiousness`, and `openness`.

## Evaluation

The grader rounds the submitted similarity scores, compares them against the gold CSV, and awards full credit when every rounded entry matches.
