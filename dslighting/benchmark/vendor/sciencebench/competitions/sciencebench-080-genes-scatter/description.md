# ScienceBench Task 80

## Overview

- Domain: Bioinformatics
- Subtask Categories: Computational Analysis, Data Visualization
- Source: scverse/scanpy-tutorials
- Output Type: Image

## Task

For the data in provided, plot a scatter plot where the x-axis is the total number of counts per cell and the y-axis is number of genes found in the cell's expression counts. Color each point by the percentage of counts in that cell that are for mitochondrial genes.

## Dataset

[START Dataset Preview: violin]
|-- violin.h5ad
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
