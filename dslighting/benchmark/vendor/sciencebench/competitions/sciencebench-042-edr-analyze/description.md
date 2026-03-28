# ScienceBench Task 42

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis, Data Visualization
- Source: neuropsychology/NeuroKit
- Output Type: Image

## Task

Derive respiratory signals from ECG data using multiple EDR methods and create a comparative visualization. Clean the ECG, detect R peaks, compute the heart period, generate EDR with four methods, and plot them together before saving the figure as a PNG file.

## Dataset

[START Dataset Preview: biosignals]
|-- bio_eventrelated_100hz.csv
[END Dataset Preview]

## Submission Format

Save a single PNG file named `sample_submission.png`.

## Evaluation

The grader compares the submitted image against the reference visualization and accepts the submission when the similarity score meets or exceeds 60.
