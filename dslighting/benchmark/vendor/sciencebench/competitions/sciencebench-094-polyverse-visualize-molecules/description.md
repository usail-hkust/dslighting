# ScienceBench Task 94

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Molecule Visualization
- Source: deepchem/deepchem
- Output Type: Image

## Task

Visualise the molecule stored in `molecule_ZINC001754572633.pkl` (an RDKit `Mol`) as a graph. Colour carbon atoms orange, oxygen atoms magenta, and nitrogen atoms cyan. Lay out the graph with NetworkX spring layout (seed=10), set node size to 800, and label each atom.

## Dataset

[START Dataset Preview: polyverse_viz]
|-- molecule_ZINC001754572633.pkl
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
