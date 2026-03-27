# ScienceBench Task 55

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Geospatial Analysis, Map Visualization
- Source: SciTools/iris
- Output Type: Image

## Task

Use the South Atlantic temperature and salinity profiles to compute a vertical section for the requested latitude/longitude window. Visualise the resulting temperature–salinity relationship and save the figure as a PNG file.

## Dataset

[START Dataset Preview: ocean_profiles]
|-- atlantic_profiles.nc
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
