# ScienceBench Task 46

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Map Visualization
- Source: rasterio/rasterio
- Output Type: Image

## Task

Use the elevation raster to compute terrain ruggedness for the study area and visualise the result. Export the final map as a PNG file.

## Dataset

[START Dataset Preview: MountainLionNew]
|-- Elevation.tif
|-- landcover_reclassified.tif
|-- ruggedness.tif
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
