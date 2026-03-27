# ScienceBench Task 8

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Selection, Data Visualization
- Source: psa-lab/predicting-activity-by-machine-learning
- Output Type: Image

## Task

Perform backward feature selection using logistic regression to identify the most relevant chemical features for predicting signal inhibition from the DKPES dataset. Binarize the signal inhibition values using an appropriate threshold, track model accuracy as features are removed, and plot accuracy versus number of retained features. 

## Dataset

The `dkpes` folder provides training and test CSV files: `dkpes_train.csv` (with signal inhibition labels and features) and `dkpes_test.csv` (features only).

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
