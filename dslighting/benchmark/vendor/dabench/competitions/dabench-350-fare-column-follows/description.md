# DABench Task 350 - Check if the Fare column follows a normal distribution.

## Task Description

Check if the Fare column follows a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `test_x.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Perform a Shapiro-Wilk test for normality on the 'Fare' column. Use a significance level (alpha) of 0.05 to determine if the 'Fare' column is normally distributed. The 'Fare' column is considered to be normally distributed if the p-value from the Shapiro-Wilk test is greater than 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `350`
- `answer`: `@is_normal[<is_normal>]` where `<is_normal>` is a boolean: True if the 'Fare' column follows a normal distribution, False otherwise.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
