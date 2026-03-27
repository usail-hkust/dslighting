# ScienceBench Task 69

## Overview

- Domain: Bioinformatics
- Subtask Categories: Dimensionality Reduction, Data Visualization
- Source: scverse/scvi-tutorials
- Output Type: Image

## Task

Process the Heart Cell Atlas subset, compute a PCA embedding, and colour the scatter plot by cell type. Save the figure as a PNG file.

## Dataset

[START Dataset Preview: hca]
|-- hca_subsampled_20k.h5ad
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
