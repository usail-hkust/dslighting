# ScienceBench Task 85

## Overview

- Domain: Bioinformatics
- Subtask Categories: Feature Engineering
- Source: mad-lab-fau/BioPsyKit
- Output Type: Tabular

## Task

Analyze the given saliva data and compute features that represent sample statistics or distribution (e.g., mean, location of max/min value, skewness) for each subject. Save the computed features along with subject condition as a dictionary of dictionaries into a json file "output file".

[START Dataset Preview: saliva_data]
|-- data.pkl
[END Dataset Preview]

## Submission Format

Save the results as a JSON file containing a nested dictionary keyed by subject IDs. Keep string fields intact and store numeric summaries as floats.

## Evaluation

The grader compares your JSON to the gold reference, checking that all numeric values match within 1e-9 relative tolerance and that categorical fields are identical.
