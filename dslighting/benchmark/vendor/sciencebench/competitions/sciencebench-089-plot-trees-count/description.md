# ScienceBench Task 89

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Map Visualization
- Source: ResidentMario/geoplot
- Output Type: Image

## Task

Use the San Francisco street-tree inventory and borough polygons to compute the percentage of missing species labels per region and visualize the results as a quadtree map similar to the reference figure.

## Dataset

[START Dataset Preview: sfo_trees_count]
|-- street_trees_sample.geojson
|-- sfo_boroughs.geojson
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
