# DABench Task 55 - What is the mean number of cases recorded across all countries and years?

## Task Description

What is the mean number of cases recorded across all countries and years?

## Concepts

Summary Statistics

## Data Description

Dataset file: `estimated_numbers.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean of the column 'No. of cases'. Convert the data type of 'No. of cases' column from Object (string) to Int64 before performing calculations. Ignore those records where 'No. of cases' column value is Null or empty.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `55`
- `answer`: `@mean_cases[<mean_value>]` where `<mean_value>` is a positive integer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
