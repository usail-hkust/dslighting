# ScienceBench Task 72

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Feature Engineering, Deep Learning
- Source: ZitongLu1996/EEG2EEG
- Output Type: NumPy array

## Task

Train the EEG2EEG model that maps neural representations from Subject 01 to Subject 03 using the provided preprocessed recordings. After fitting the model with the training data, run inference on the Subject 01 test set and generate the corresponding Subject 03 responses.

## Dataset

[START Dataset Preview: thingseeg2]
|-- train/sub01.npy
|-- train/sub03.npy
|-- test/sub01.npy
[END Dataset Preview]

## Submission Format

Save the normalized Subject 03 predictions as a NumPy array with shape `(200, 3400)`.

## Evaluation

The grader loads your NumPy array, applies the same normalization as the reference implementation, and compares it to the gold array. A submission is accepted when the Spearman correlation reaches at least 0.73.
