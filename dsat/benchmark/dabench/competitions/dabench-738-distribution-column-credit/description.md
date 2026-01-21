# DABench Task 738 - Check if the distribution of the "Age" column in the Credit.csv file adheres to a normal distribution.

## Task Description

Check if the distribution of the "Age" column in the Credit.csv file adheres to a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `Credit.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Shapiro-Wilk test from scipy.stats library to test for normality. Use a significance level (alpha) of 0.05. If the p-value is less than the significance level, declare that the distribution is not normal. Otherwise, declare that the distribution is normal.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@is_normal[is_normal]

where "is_normal" is a string that can be either "Normal" or "Not Normal" based on the Shapiro-Wilk test result.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
