# DABench Task 174 - Determine the skewness of the fares paid by the passengers on the Titanic.

## Task Description

Determine the skewness of the fares paid by the passengers on the Titanic.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

For the calculation of skewness, use the pandas DataFrame method skew(). No other method should be employed for calculation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `174`
- `answer`: `@fare_skewness[<fare_skew_value>]` where the value is rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
