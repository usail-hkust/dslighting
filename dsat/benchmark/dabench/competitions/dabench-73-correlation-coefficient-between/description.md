# DABench Task 73 - Calculate the correlation coefficient between the "High" and "Low" columns.

## Task Description

Calculate the correlation coefficient between the "High" and "Low" columns.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `microsoft.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Pearson correlation coefficient for computation. Round the result to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `73`
- `answer`: `@correlation_coefficient[<correlation_coefficient>]` rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
