# ScienceBench Task 83

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Geospatial Analysis, Map Visualization
- Source: https://github.com/GeoStat-Framework/PyKrige
- Output Type: Image

## Task

Your task is to analyze urban heat using Kriging interpolation techniques in Python. The analysis should focus on understanding spatial patterns of urban heat islands by using point temperature data and interpolating these values across a city. You also have to use a demographical layer to extract and enhance the data visualization on the elder group. Your goal is to load the temperature sample data, apply the Kriging method to predict temperature across the urban area, and generate a choropleth map showing the average interpolated temperature surface in each census block group. The final output should be saved as "output file".

## Dataset

[START Dataset Preview: UrbanHeat]
|-- block.geojson
|-- Temperature.geojson
[END Dataset Preview]


## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
