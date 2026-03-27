# ScienceBench Task 10

## Overview

- Domain: Geographical Information Science
- Subtask Categories: Geospatial Analysis, Map Visualization
- Source: geopandas/geopandas
- Output Type: Image

## Task

Analyze Toronto fire stations and their service coverage, identifying potential coverage gaps. Visualize the results.

## Dataset

{"type":"FeatureCollection","features":[{"type":"Feature","id":1,"geometry":{"type":"Point","coordinates":[-79.163608108967836,43.794228005499171]},"properties":{"OBJECTID_1":1,"NAME":"FIRE STATION 214","ADDRESS":"745 MEADOWVALE RD","WARD_NAME":"Scarborough East (44)","MUN_NAME":"Scarborough"}},{"type":"Feature","id":2,"geometry":{"type":"Point","coordinates":[-79.148072382066644,43.777409170303173]},"properties":{"OBJECTID_1":2,"NAME":"FIRE STATION 215","ADDRESS":"5318 LAWRENCE AVE E","WARD_NAME":"Scarborough East (44)","MUN_NAME":"Scarborough"}},{"type":"Feature","id":3,"geometry":{"type":"Point","coordinates":[-79.255069254032705,43.734807353775956]},"properties":{"OBJECTID_1":3,"NAME":"FIRE STATION 221","ADDRESS":"2575 EGLINTON AVE E","WARD_NAME":"Scarborough Southwest (35)","MUN_NAME":"Scarborough"}},...]}


## Submission Format

Save the output PNG file.

## Evaluation

The grader compares the submitted image against the gold visualization using LLM as judge (threshold 60/100).
