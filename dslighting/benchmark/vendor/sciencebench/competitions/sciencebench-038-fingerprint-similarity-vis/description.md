# Fingerprint Similarity Visualization

## Overview

This task focuses on visualizing the Tanimoto similarities of protein-ligand interaction fingerprints across trajectory frames.

## Task Description

Plot the Tanimoto similarities of the fingerprint between the frames. Specifically, analyze the interaction fingerprints between a selected ligand and protein for the first 10 trajectory frames.

## Dataset

The dataset contains molecular dynamics trajectory data:
- `top.pdb`: Protein structure topology file (~500 KB)
- `traj.xtc`: Trajectory file with multiple frames (~4.8 MB)

Files are located in the public data directory.

## Task Requirements

1. Load the protein structure (`top.pdb`) and trajectory (`traj.xtc`)
2. Extract interaction fingerprints between ligand and protein for the first 10 frames
3. Calculate Tanimoto similarities between consecutive frames
4. Generate a visualization showing the similarity values
5. Save the figure as a PNG file

## Tools and Libraries

You may use **ProLIF** for analyzing protein-ligand interactions. ProLIF is built upon MDAnalysis and is capable of analyzing protein-ligand interactions.

Reference: https://github.com/chemosim-lab/ProLIF

## Evaluation

Your submission will be evaluated by comparing your generated figure with the gold standard figure using visual similarity metrics. The score must be >= 60 (out of 100) to pass.
