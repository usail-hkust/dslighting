# ScienceBench Task 33

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Map Visualization
- Source: geopandas/geopandas
- Output Type: Image

## Task

Overlay the bus service areas with block-level demographic layers (poverty, density, vehicle access) for Hamilton County, Tennessee. Derive transit accessibility indicators from the intersections and summarize them in the submission map with clear legends, labels, and context.

## Dataset

[START Dataset Preview: TransitAccessDemographic]
|-- BusServiceArea.geojson
|-- HamiltonDemographics.geojson
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
