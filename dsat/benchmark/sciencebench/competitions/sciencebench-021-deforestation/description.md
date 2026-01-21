# ScienceBench Task 21

## Overview

- Domain: Environmental Science
- Subtask Categories: Geospatial Analysis, Forecasting
- Source: WWF/Deforestation monitoring
- Output Type: Tabular

## Task

Estimate the percentage of forest area lost within the provided region using the supplied geospatial layers. Build any workflows required to analyse the deforestation risk and produce a single percentage value, keeping the original data ordering intact.

## Dataset

The `deforestation/` directory contains the layers needed for the analysis:

- `deforestedArea.geojson` – polygons representing detected deforested area.
- `roads.geojson` – road network segments in the study region.

## Evaluation

Your submission must report a single `percentage_deforestation` value that matches the reference calculation. The grader reports `1 - relative_error`, where relative error is computed against the gold percentage. Values outside the expected order result in a zero score.