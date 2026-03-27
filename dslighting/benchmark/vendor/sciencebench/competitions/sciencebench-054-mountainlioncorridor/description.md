# ScienceBench Task 54

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Map Visualization
- Source: rasterio/rasterio
- Output Type: Image

## Task

Combine ruggedness, road distance, reclassified land cover, and protected status into a cost surface that highlights mountain lion movement corridors. Produce a visual overlay of the corridor and export it as a PNG file.

## Dataset

[START Dataset Preview: MountainLionNew]
|-- distance.tif
|-- distance_to_roads.tif
|-- landcover_reclassified.tif
|-- protected_status_reclassified.tif
|-- ruggedness.tif
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
