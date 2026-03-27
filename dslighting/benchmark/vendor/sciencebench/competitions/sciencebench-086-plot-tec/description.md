# ScienceBench Task 86

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Map Visualization
- Source: SciTools/iris
- Output Type: Image

## Task

Load Total Electron Content (TEC) data from a space weather NetCDF file and visualize it as a filled contour map with a geographical and coastline background.

## Dataset

[START Preview of total_electron_content/space_weather.nc]
 rLat: [-45, -42, -39, ...]
 rLon: [-44.47640122, -41.47640122, -38.47640122, ...]
 latitude: [[-8.234822544843928, -7.203030736424036, -6.232759519501953, ...]...]
 longitude: [[--, --, --, ...]...]
 TEC: [[-1.512660e+01, -1.212091e+01, -9.138200e+00, ...]...]
 ...
 [END Preview of total_electron_content/space_weather.nc]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
