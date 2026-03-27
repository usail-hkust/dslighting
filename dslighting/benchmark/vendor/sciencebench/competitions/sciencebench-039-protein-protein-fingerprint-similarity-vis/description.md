# ScienceBench Task 39

## Overview

- Domain: Computational Chemistry
- Subtask Categories: Computational Analysis, Data Visualization
- Source: chemosim-lab/ProLIF
- Output Type: Image

## Task

Plot the Tanimoto similarities of the fingerprint between the frames. Specifically, the interaction fingerprints between a selected small protein and large protein for the first 10 trajectory frames.

## Dataset

N/A

## Submission Format

Save columns `file_name` and `image_base64`. Encode the output PNG as base64 (UTF-8 string) and place it in the row for that filename.

## Evaluation

The grader decodes your base64 image, rescales it to the reference size, and computes a similarity score between 0 and 1.
