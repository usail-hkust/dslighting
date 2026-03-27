# ScienceBench Task 17

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Feature Engineering, Statistical Analysis, Data Visualization
- Source: martin-sicho/papyrus-scaffold-visualizer
- Output Type: Image

## Task

Use the provided Papyrus A2A receptor ligand data to project the chemical space into two dimensions (for example via PCA, t-SNE, or UMAP). Color each point by the associated activity value and render a clear scatter plot summarizing the chemical space. Save the final visualization to the required PNG output path.

## Dataset

The `papyrus_vis/` folder contains `A2AR_LIGANDS.tsv` with SMILES strings, Papyrus identifiers, and measured activity classes for A2A receptor ligands.

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
