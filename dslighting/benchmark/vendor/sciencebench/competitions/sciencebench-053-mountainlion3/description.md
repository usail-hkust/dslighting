# ScienceBench Task 53

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Geospatial Analysis
- Source: rasterio/rasterio
- Output Type: Raster

## Task

Reclassify the provided land-cover and protected-status rasters to a common 1–10 scale suitable for mountain lion habitat analysis. Save the reclassified outputs as GeoTIFF files.

## Dataset

[START Dataset Preview: MountainLionNew]
|-- Elevation.tif
|-- Mountain_Lion_Habitat.geojson
|-- Protected_Status.tif
|-- distance_to_roads.tif
|-- landCover.tif
[END Dataset Preview]

## Submission Format

Save a submission directory containing exactly these two GeoTIFF files:

- `landCover_reclassified.tif`
- `protected_status_reclassified.tif`

## Evaluation

The grader compares both submitted rasters against the reference rasters and awards full credit when each raster matches more than 70% of the reference cells.
