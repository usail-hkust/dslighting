# ScienceBench Task 52

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Feature Engineering, Deep Learning, Molecule Visualization
- Source: deepchem/deepchem
- Output Type: Image

## Task

Visualise the aquatic toxicity QSAR dataset by highlighting atomic contributions for the provided test compound. Export the figure as a PNG file.

## Dataset

[START Dataset Preview: aquatic_toxicity]
|-- Tetrahymena_pyriformis_OCHEM.sdf
|-- Tetrahymena_pyriformis_OCHEM_test_ex.sdf
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
