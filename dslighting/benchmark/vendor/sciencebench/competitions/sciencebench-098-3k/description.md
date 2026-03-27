# ScienceBench Task 98

## Overview

- Domain: Bioinformatics
- Subtask Categories: Computational Analysis, Data Visualization
- Source: scverse/scirpy
- Output Type: Image

## Task

Compute chain quality control information for this single-cell TCR/RNA-seq data collected from resected tumors, histologically normally adjacent tissues (NAT), and peripheral blood. Then, draw a stacked bar chart of the number of cells in each chain pairing, coloring each portion of the stack by the source (tumor, NAT, or blood).

## Dataset

[START Dataset Preview: cell_3k]
|-- 3kdata.h5mu
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
