# DABench Task 71 - Calculate the mean and standard deviation of the "Volume" column.

## Task Description

Calculate the mean and standard deviation of the "Volume" column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `microsoft.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the built-in functions in Python's pandas library for computation. Round the result to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `71`
- `answer`: `@mean_volume[<mean_volume>] @std_dev_volume[<std_dev_volume>]`, both rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
