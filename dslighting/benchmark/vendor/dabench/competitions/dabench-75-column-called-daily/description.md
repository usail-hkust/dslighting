# DABench Task 75 - Create a new column called "Daily Return" that calculates the percentage change in the "Close" price from the previous day. Calculate the mean and standard deviation of the "Daily Return" column.

## Task Description

Create a new column called "Daily Return" that calculates the percentage change in the "Close" price from the previous day. Calculate the mean and standard deviation of the "Daily Return" column.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `microsoft.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate "Daily Return" as ((Close price of today - Close price of previous day) / Close price of previous day) * 100. Calculate mean and standard deviation to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `75`
- `answer`: two key-value pairs separated by a space: `@daily_return_std[<std>] @daily_return_mean[<mean>]`

Both values are rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
