# ScienceBench Task 77

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Statistical Analysis, Map Visualization
- Source: Solve-Geosolutions/transform_2022
- Output Type: Image

## Task

Model water quality using spatial interpolation techniques in Python. The analysis should focus on understanding spatial patterns of water quality by using point sample data and interpolating these values across a broader area including unsampled locations. Your goal is to load the water quality sample data, and apply appropriate spatial interpolation methods, such as Kriging, to predict water quality across the region. The final output should be a map showing the interpolated water quality surface, saved as "output file"

## Dataset

[START Dataset Preview: WaterQuality]
|-- Bay.geojson
|-- DissolvedO2.geojson
[END Dataset Preview]


## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
