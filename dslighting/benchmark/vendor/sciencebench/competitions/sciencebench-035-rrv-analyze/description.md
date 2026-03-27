# ScienceBench Task 35

## Overview

- Domain: Psychology and Cognitive science
- Subtask Categories: Computational Analysis
- Source: neuropsychology/NeuroKit
- Output Type: Tabular

## Task

Perform RRV analysis on the recordings. Clean the respiration (RSP) signal, extract inhalation peaks and respiratory rate, and compute time-, frequency-, and non-linear domain metrics. Store the feature table as a CSV file.

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

The grader checks that at least 60 % of feature columns match the reference within an absolute summed error of 1.0. Submissions below this threshold fail.
