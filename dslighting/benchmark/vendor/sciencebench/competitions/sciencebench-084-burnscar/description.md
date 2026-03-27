# ScienceBench Task 84

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Computational Analysis, Map Visualization
- Source: rasterio/rasterio
- Output Type: Image

## Task

Assess burn scars using satellite imagery and perform spatial analysis to understand the impact of wildfires. The goal is to use the satellite imagery data from 2014 and 2015 on analyzing burn scars by determining the change in Normalized Burn Ratio, and generate a map that visualizes the spatial extent of the damage areas in vector data format (i.e., polygons). The final output should be a visual representation of the burn scars, saved as "output file".

## Dataset

[START Dataset Preview: BurnScar]
|-- G_2014.tif
|-- G_2015.tif
|-- study_area.geojson
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
