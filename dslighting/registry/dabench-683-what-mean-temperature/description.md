# DABench Task 683 - 1. What is the mean temperature recorded in the dataset?

## Task Description

1. What is the mean temperature recorded in the dataset?

## Concepts

Summary Statistics

## Data Description

Dataset file: `ravenna_250715.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean temperature to two decimal places. No missing values in the temperature data.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@mean_temperature[value]

"value" is the mean temperature rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
