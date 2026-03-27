# ScienceBench Task 50

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Computational Analysis, Data Visualization
- Source: ajdawson/eofs/
- Output Type: Image

## Task

Compute and plot the leading EOF of sea surface temperature anomalies using the xarray workflow, including the associated principal component time series. Export the figure as a PNG file.

## Dataset

[START Dataset Preview: EOF_xarray_sst]
|-- sst_ndjfm_anom.nc
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
