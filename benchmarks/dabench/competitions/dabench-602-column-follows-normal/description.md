# DABench Task 602 - 2. Check if the RHO_OLD column follows a normal distribution.

## Task Description

2. Check if the RHO_OLD column follows a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `well_2_complete.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Shapiro-Wilk test to evaluate if the RHO_OLD column follows a normal distribution. In the test, if the p-value is less than 0.05, then it does not follow a normal distribution. If the p-value is greater than 0.05, then it follows a normal distribution.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@normality_status[status]

where "status" is "Normal" if the p-value > 0.05, or "Not Normal" if p-value < 0.05.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
