# ScienceBench Task 92

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: brand-d/cogsci-jnmf
- Output Type: JSON

## Task

Compute summary metrics from the JNMF factor matrices (common error/importance, high importance, low importance, distinct error/importance) following the specification in the task prompt. Store the six scores in a JSON object keyed by metric name.

## Dataset

[START Dataset Preview: jnmf_visualization]
|-- fit_result_conscientiousness_W_high.npy
|-- fit_result_conscientiousness_W_low.npy
|-- fit_result_conscientiousness_H_high.npy
|-- fit_result_conscientiousness_H_low.npy
[END Dataset Preview]

## Submission Format

Save the metrics as a JSON file. Numerical values should be floats.

## Evaluation

The grader compares each metric with the gold JSON using an absolute tolerance of 1e-4. All keys must be present and within tolerance.
