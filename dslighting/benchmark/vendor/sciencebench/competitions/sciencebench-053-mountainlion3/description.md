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

Save columns `file_name` and `image_base64`. Include one row for each output raster and encode the GeoTIFF bytes as base64 strings.

## Evaluation

The grader decodes both rasters, compares them with the reference reclassified arrays, and awards full credit when each raster matches more than 70% of the reference cells.
