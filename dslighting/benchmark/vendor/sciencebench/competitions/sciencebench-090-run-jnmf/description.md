# ScienceBench Task 90

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: brand-d/cogsci-jnmf
- Output Type: NumPy arrays

## Task

Perform a joint non-negative matrix factorization on the provided conscientiousness features. Factor `X1_conscientiousness.npy` into `W_high` and `H_high`, and `X2_conscientiousness.npy` into `W_low` and `H_low`. Ensure all factors are non-negative and reconstruct the inputs closely.

## Dataset

[START Dataset Preview: jnmf_data]
|-- X1_conscientiousness.npy
|-- X2_conscientiousness.npy
[END Dataset Preview]

## Submission Format

Save the four factor matrices as NumPy files with the exact names:
- `fit_result_conscientiousness_W_high.npy`
- `fit_result_conscientiousness_H_high.npy`
- `fit_result_conscientiousness_W_low.npy`
- `fit_result_conscientiousness_H_low.npy`

## Evaluation

The grader checks non-negativity and measures reconstruction error for each input (thresholds: X1 < 34, X2 < 32). Both conditions must be satisfied to receive credit.
