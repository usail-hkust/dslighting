# DABench Task 10 - Check if the "Total Traded Quantity" column adheres to a normal distribution.

## Task Description

Check if the "Total Traded Quantity" column adheres to a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `GODREJIND.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use Shapiro-Wilk test from scipy.stats module to check for normality. In this test, the null hypothesis is that the data was drawn from a normal distribution. An alpha level of 0.05 (5%) should be taken as the significance level. If the p-value is less than the alpha level, the null hypothesis is rejected and the data does not follow a normal distribution. If the p-value is greater than the alpha level, the null hypothesis is not rejected and the data may follow a normal distribution.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `10`
- `answer`: `@is_normal[<yes/no>]` indicating whether the data follows a normal distribution.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
