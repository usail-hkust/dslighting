# DABench Task 304 - Check if the fare variable follows a normal distribution.

## Task Description

Check if the fare variable follows a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Shapiro-Wilk test to check for normality. The null hypothesis for this test is that the data is normally distributed. If the p-value is less than 0.05, reject the null hypothesis and conclude that the data is not normally distributed. If the p-value is greater than 0.05, fail to reject the null hypothesis and conclude that the data is normally distributed.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `304`
- `answer`: `@normality_test_result[<True/False>]`, a boolean indicating whether the fare variable follows a normal distribution.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
