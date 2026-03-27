# ScienceBench Task 26

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Computational Analysis
- Source: chemosim-lab/ProLIF
- Output Type: Tabular

## Task

Generate the interaction fingerprints between a selected ligand and protein for the first 10 trajectory frames. Combine the ligand, protein, type of interactions, and frame index into a name in the output CSV file. Additionally, save the status of the fingerprint under the column Y.
## Dataset

N/A

## Submission Format

Save predictions with the same header and column order as the template. Ensure numeric columns retain their dtype and identifiers remain aligned.

## Evaluation

Negative root mean squared error (closer to zero is better).
