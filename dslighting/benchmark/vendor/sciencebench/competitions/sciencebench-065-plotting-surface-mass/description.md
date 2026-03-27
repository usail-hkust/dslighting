# ScienceBench Task 65

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Geospatial Analysis, Data Visualization
- Source: OGGM/tutorials
- Output Type: Image

## Task

Generate a time-series plot of OGGM surface mass balance for glacier `RGI60-11.00001`, covering 1960–2020. Save the figure as a PNG file.

## Dataset

[START Dataset Preview: ocean_glacier]
|-- RGI60-11.00001/model_diagnostics_historical.nc
|-- RGI60-11.00001/model_diagnostics_spinup_historical.nc
|-- RGI60-11.00001/reference_mb_results.csv
|-- RGI60-11.00001/gridded_data.nc
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
