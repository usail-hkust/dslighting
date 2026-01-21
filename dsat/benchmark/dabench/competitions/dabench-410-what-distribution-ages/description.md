# DABench Task 410 - What is the distribution of ages among the male passengers who did not survive? Is it significantly different from the distribution of ages among the female passengers who did not survive?

## Task Description

What is the distribution of ages among the male passengers who did not survive? Is it significantly different from the distribution of ages among the female passengers who did not survive?

## Concepts

Distribution Analysis

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculating the distribution of ages should use a Kernel Density Estimation (KDE) method. Perform a two-sample Kolmogorov-Smirnov test to compare the distributions. Use a significance level (alpha) of 0.05. If the p-value is less than 0.05, conclude the distributions are significantly different. If the p-value is greater than or equal to 0.05, conclude the distributions are not significantly different.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@is_significantly_different[answer]

"answer" is a boolean indicating the result of the test. If the distributions are significantly different, use "True"; otherwise "False".

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
