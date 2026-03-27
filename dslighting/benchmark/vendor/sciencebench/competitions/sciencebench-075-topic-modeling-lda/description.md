# ScienceBench Task 75

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering, Machine Learning, Data Visualization
- Source: scverse/scvi-tutorials
- Output Type: Image

## Task

Train the amortized Latent Dirichlet Allocation (LDA) model with 10 topics on the PBMC 10K dataset. After fitting the model, compute topic proportions for every cell and visualise them with UMAP, highlighting the learned topics.

## Dataset

[START Dataset Preview: pbmc]
|-- pbmc_10k_protein_v3.h5ad
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
