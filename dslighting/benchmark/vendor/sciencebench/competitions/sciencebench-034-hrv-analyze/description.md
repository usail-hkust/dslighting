# ScienceBench Task 34

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: neuropsychology/NeuroKit
- Output Type: Tabular

## Task

Use `bio_eventrelated_100hz.csv` and `bio_resting_5min_100hz.csv` to compute heart rate variability (HRV) indices spanning time, frequency, and non-linear domains. Detect ECG peaks, derive the full feature set, and write the resulting table.

## Dataset

[START Dataset Preview: biosignals]
|-- bio_eventrelated_100hz.csv
|-- bio_resting_5min_100hz.csv
|-- ecg_1000hz.csv
|-- eog_100hz.csv
[END Dataset Preview]

## Submission Format

Save predictions with the same header and column order as the template. Ensure numeric columns retain their dtype and identifiers remain aligned.

## Evaluation

The grader checks that at least 90 % of feature columns match the reference within an absolute summed error of 0.5. Submissions below this threshold fail.
