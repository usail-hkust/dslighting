# ScienceBench Task 63

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Signal Processing, Data Visualization
- Source: neuropsychology/NeuroKit
- Output Type: Image

## Task

Extract heart-rate and respiration-rate intervals from the biosignals recordings, then visualise both modalities. Produce a PNG to summarise the ECG analysis and another PNG to summarise the respiration analysis.

## Dataset

[START Dataset Preview: biosignals]
|-- bio_eventrelated_100hz.csv
|-- bio_resting_5min_100hz.csv
|-- ecg_1000hz.csv
|-- eog_100hz.csv
[END Dataset Preview]

## Submission Format

Save a submission directory containing exactly these two PNG files:

- `bio_ecg_plot.png`
- `bio_rsp_plot.png`

## Evaluation

The grader compares both submitted images against the corresponding reference plots and grants full credit when each similarity score meets or exceeds 60.
