# ScienceBench Task 74

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Geospatial Analysis, Data Visualization
- Source: OGGM/oggm
- Output Type: Image

## Task

I would like to simulate and display the change of glacier area and thickness for region 'RGI60-15.04847'. Use the OGGM library and perform a random simulation from year 2020 to year 2060. Use the data from year 1999 as your starting point and set halfsize to 5. Use 1.8 as the temperature bias. Show a comparison of distributed thickness from year 2020, 2040, and 2060 in three subplots. Set the maximum value of thickness to 300.

## Dataset

[START Dataset Preview: ocean_glacier]
|-- RGI60-11.00001/elevation_band_flowline.csv
|-- RGI60-11.00001/model_diagnostics_historical.nc
|-- RGI60-11.00001/model_flowlines_dyn_melt_f_calib.pkl
|-- RGI60-11.00001/gridded_data.nc
[END Dataset Preview]

## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
