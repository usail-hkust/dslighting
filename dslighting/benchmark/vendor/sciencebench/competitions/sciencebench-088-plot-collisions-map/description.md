# ScienceBench Task 88

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Map Visualization
- Source: ResidentMario/geoplot
- Output Type: Image

## Task

Use the provided NYC fatal collision records and borough boundaries to create a choropleth or point map that highlights the 2016 fatal crashes. Match the styling of the reference figure that overlays incidents on the city map.

## Dataset

[START Dataset Preview: nyc_collisions_map]
|-- fatal_collisions.geojson
|-- nyc_boroughs.geojson
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
