# ScienceBench Task 91

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Data Visualization
- Source: brand-d/cogsci-jnmf
- Output Type: Image

## Task

Use the provided factor matrices to visualise conscientiousness patterns extracted via joint NMF. Plot the high, shared, and low patterns as three heatmaps (left to right), each reshaped from a vector into a 64 × 9 grid.

## Dataset

[START Dataset Preview: jnmf_visualization]
|-- fit_result_conscientiousness_W_high.npy
|-- fit_result_conscientiousness_W_low.npy
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
