# ScienceBench Task 9

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Statistical Analysis, Data Visualization
- Source: deepchem/deepchem
- Output Type: Image

## Task

Load the FACTORS dataset, compute the Pearson correlation coefficient between each task and every other task, and visualize the distribution of correlation values as a histogram. 

## Dataset

Molecule,D_00001,D_00002,D_00003,D_00004,D_00005, ...
M_0164851,0,0,0,0,0, ...
M_0164852,0,0,0,0,0, ...
...

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
