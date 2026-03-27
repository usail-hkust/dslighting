# ScienceBench Task 81

## Overview

- Domain: Bioinformatics
- Subtask Categories: Data Visualization
- Source: scverse/scanpy-tutorials
- Output Type: Image

## Task

For the given gene expression dataset, perform a scatter plot in UMAP basis to visualize groups of cells that express popular marker genes across various cell types: T-cell, B-cell, plasma, monocytes and dendritic. Also add plots for number of UMI counts per cell and bulk labels per cell.

## Dataset

[START Dataset Preview: pbmc_umap]
|-- pbmc.h5ad
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
