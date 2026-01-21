# DABench Task 72 - Check if the "Close" column adheres to a normal distribution.

## Task Description

Check if the "Close" column adheres to a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `microsoft.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Shapiro-Wilk test to assess the normality of the "Close" column. If the p-value is less than 0.05, consider the data to be non-normally distributed. Otherwise, consider it to be normally distributed.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `72`
- `answer`: `@normality_test_result[<Normal/Non-normal>]` based on the Shapiro-Wilk test.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
