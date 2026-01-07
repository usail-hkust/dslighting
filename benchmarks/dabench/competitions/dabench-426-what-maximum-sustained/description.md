# DABench Task 426 - 2. What is the maximum sustained wind speed recorded during the storm with the highest maximum storm category?

## Task Description

2. What is the maximum sustained wind speed recorded during the storm with the highest maximum storm category?

## Concepts

Summary Statistics, Correlation Analysis

## Data Description

Dataset file: `cost_data_with_errors.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Firstly, identify the storm with the highest maximum storm category, neglecting any ties. If there are multiple storms with the same highest maximum storm category, choose the one that appears first in the given dataset. Then find the maximum sustained wind speed corresponding to this particular storm.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@max_wind_speed[number]

"number" is a float with two decimal places indicating the highest wind speed recorded for the storm with the highest maximum storm category.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
