# DABench Task 244 - Are the number of home runs hit by the players normally distributed?

## Task Description

Are the number of home runs hit by the players normally distributed?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `baseball_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Assess whether the data is normally distributed using the Shapiro-Wilk test for normality with a significance level (alpha) of 0.05. Exclude the player with a missing value of home runs in your calculations. 
If the p-value is less than 0.05, report that the distribution is not normal. If the p-value is greater than or equal to 0.05, report that the distribution is normal.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `244`
- `answer`: `@normality_test[<normality_test>]` where `<normality_test>` is `normal` or `not_normal` based on the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
