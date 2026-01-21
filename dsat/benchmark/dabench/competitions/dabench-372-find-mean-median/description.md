# DABench Task 372 - 1. Find the mean and median of the "Trips over the past 24-hours (midnight to 11:59pm)" column.

## Task Description

1. Find the mean and median of the "Trips over the past 24-hours (midnight to 11:59pm)" column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `2014_q4.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Both mean and median should be calculated by the built-in Python function, not manually. The result should be rounded to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `372`
- `answer`: `@mean[<mean_value>]` where `<mean_value>` is the mean value rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
