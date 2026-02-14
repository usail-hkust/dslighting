# DABench Task 446 - 1. What is the mean wind speed in the dataset?

## Task Description

1. What is the mean wind speed in the dataset?

## Concepts

Summary Statistics

## Data Description

Dataset file: `baro_2015.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the arithmetic mean of WINDSPEED, excluding any null values. The mean must be calculated to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@mean_windspeed[mean_windspeed]

"mean_windspeed" is a number with a maximum of three decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
