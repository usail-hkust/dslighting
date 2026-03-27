# ScienceBench Task 76

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Feature Engineering, Machine Learning, Map Visualization
- Source: Solve-Geosolutions/transform_2022
- Output Type: Image

## Task

Run a random-forest-based prospectivity analysis for tin–tungsten deposits across Tasmania. Prepare the geospatial layers, train and validate the classifier, and generate a probability map that highlights prospective areas. Target an AUC of at least 0.9 before exporting your final visualization.

## Dataset

[START Dataset Preview: MineralProspectivity]
|-- sn_w_minoccs.gpkg
|-- tasgrav_IR.tif
|-- tasmag_TMI.tif
|-- tasrad_K_pct.tif
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
