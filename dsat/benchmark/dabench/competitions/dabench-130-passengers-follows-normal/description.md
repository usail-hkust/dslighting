# DABench Task 130 - Check if the age of the passengers follows a normal distribution.

## Task Description

Check if the age of the passengers follows a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Shapiro-Wilk test to check the normality of the age distribution. Ignore the null values. The null hypothesis of this test is that the population is normally distributed. If the p value is less than 0.05, the null hypothesis is rejected and there is evidence that the data tested are not normally distributed. On the other hand, if the p value is greater than 0.05, then the null hypothesis that the data came from a normally distributed population cannot be rejected.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `130`
- `answer`: `@is_normal[<True/False>]` indicating whether the age values follow a normal distribution.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
