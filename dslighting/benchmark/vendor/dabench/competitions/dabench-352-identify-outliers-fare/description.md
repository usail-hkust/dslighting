# DABench Task 352 - Identify any outliers in the Fare column using the Z-score method.

## Task Description

Identify any outliers in the Fare column using the Z-score method.

## Concepts

Outlier Detection

## Data Description

Dataset file: `test_x.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Z-score for each value in the Fare column. 
Consider a value to be an outlier if its Z-score is greater than 3 or less than -3.
Return the list of outlier values sorted in ascending order.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `352`
- `answer`: `@fare_outliers[<outliers_list>]` where `<outliers_list>` is a comma-separated list of integers in ascending order (empty if none).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
