# DABench Task 588 - Are there any outliers in the average wait time for callers before being answered by an agent? If so, how many outliers are there?

## Task Description

Are there any outliers in the average wait time for callers before being answered by an agent? If so, how many outliers are there?

## Concepts

Outlier Detection

## Data Description

Dataset file: `20170413_000000_group_statistics.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Detect the outliers using the Z-score method. Consider any data point with an absolute Z-score value greater than 3 as an outlier.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `588`
- `answer`: `@num_of_outliers[<number_of_outliers>]` where `<number_of_outliers>` is a non-negative integer detected via the Z-score method.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
