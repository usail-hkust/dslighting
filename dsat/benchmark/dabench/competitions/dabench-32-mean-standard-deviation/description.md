# DABench Task 32 - Calculate the mean and standard deviation of the "importance.score" column.

## Task Description

Calculate the mean and standard deviation of the "importance.score" column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `imp.score.ldlr.metabolome.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean and standard deviation to two decimal places for the "importance.score" column. Ignore any null or missing values in the calculations. The calculations are to be done using standard statistical methods without applying any transformations or filters to the data.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `32`
- `answer`: two key-value pairs separated by a space: `@importance_score_std[<std_dev>] @importance_score_mean[<mean>]`

Both values are non-negative numbers rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
