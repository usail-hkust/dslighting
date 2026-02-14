# DABench Task 0 - Calculate the mean fare paid by the passengers.

## Task Description

Calculate the mean fare paid by the passengers.

## Concepts

Summary Statistics

## Data Description

Dataset file: `test_ave.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean fare using Python's built-in statistics module or appropriate statistical method in pandas. Rounding off the answer to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `0`
- `answer`: `@mean_fare[<mean_fare_value>]` where the value is rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
