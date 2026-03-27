# ScienceBench Task 32

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Computational Analysis, Data Visualization
- Source: rasterio/rasterio
- Output Type: Image

## Task

Derive slope and aspect rasters from `CatalinaBathymetry.tif`, join those measurements to the coral and sponge observations, and aggregate mean slope/aspect per species. Present the summary in the submission image expected by the template, including clear legends, units, and map context for Catalina Island.

## Dataset

[START Dataset Preview: CoralSponge]
|-- CatalinaBathymetry.tif
|-- CatalinaBathymetry.tif.aux.xml
|-- CatalinaBathymetry.tif.vat.cpg
|-- CatalinaBathymetry.tif.vat.dbf
|-- CatalinaBathymetry.tfw
|-- CoralandSpongeCatalina.geojson
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
