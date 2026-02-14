# DABench Task 578 - What is the average trading volume of AAPL stock?

## Task Description

What is the average trading volume of AAPL stock?

## Concepts

Summary Statistics

## Data Description

Dataset file: `e5_aapl.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean trading volume ("Volume") of all available records. Do not consider any values as outliers.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `578`
- `answer`: `@mean_volume[<mean volume>]`, a decimal number rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
