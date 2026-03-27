# ScienceBench Task 71

## Overview

- Domain: Psychology and Cognitive Science
- Subtask Categories: Feature Engineering, Machine Learning
- Source: ZitongLu1996/EEG2EEG
- Output Type: NumPy array

## Task

Learn a linear mapping from Subject 01 to Subject 03 EEG representations using the provided ThingseEG2 training splits. Fit the model on the paired training recordings, apply it to the Subject 01 test data, and save the generated Subject 03 signals as the required NumPy file.

## Dataset

[START Dataset Preview: thingseeg2]
|-- train/sub01.npy
|-- train/sub03.npy
|-- test/sub01.npy
[END Dataset Preview]

## Submission Format

Save the predictions as a NumPy array shaped like the provided test data (200 × 3400 after reshaping).

## Evaluation

Submissions are accepted when the Spearman correlation between the generated signals and the normalized gold signals reaches at least 0.6 (matching the reference evaluation script).
