# ScienceBench Task 96

## Overview

- Domain: Bioinformatics
- Subtask Categories: Data Visualization
- Source: scverse/scanpy-tutorials
- Output Type: Image

## Task

Analyze the preprocessed PBMC dataset with precomputed UMAP components for 700 cells and 765 highly variable genes. Compute clusters using the Leiden method and visualize the clustering results with UMAP. Save the figure to "output file".

## Dataset

[START Preview of pbmc68k/pbmc68k_reduced.h5ad, which is an AnnData object]

AnnData object with n_obs × n_vars = 700 × 765
    obs: 'bulk_labels', 'n_genes', 'percent_mito', 'n_counts', 'S_score', 'G2M_score', 'phase', 'louvain'
    var: 'n_counts', 'means', 'dispersions', 'dispersions_norm', 'highly_variable'
    uns: 'bulk_labels_colors', 'louvain', 'louvain_colors', 'neighbors', 'pca', 'rank_genes_groups'
    obsm: 'X_pca', 'X_umap'
    varm: 'PCs'
    obsp: 'distances', 'connectivities'

[END Preview of pbmc68k/pbmc68k_reduced.h5ad]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
