# ScienceBench Task 100

## Overview

- Domain: Bioinformatics
- Subtask Categories: Statistical Analysis, Data Visualization
- Source: scverse/scanpy-tutorials
- Output Type: Image

## Task

You should visualize the data in spatial coordinates in three figures colored by total_counts, n_genes_by_counts, and clusters, respectively.

## Dataset

[START Preview of lymph/lymph_node.h5ad, which is an AnnData object]

MuData object with n_obs × n_vars = 3000 × 30727
  2 modalities
    gex:        3000 x 30727
      obs:        'cluster_orig', 'patient', 'sample', 'source'
      uns:        'cluster_orig_colors'
      obsm:        'X_umap_orig'
    airr:        3000 x 0
      obs:        'high_confidence', 'is_cell', 'clonotype_orig'
      obsm:        'airr'

[END Preview of lymph/lymph_node.h5ad]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
