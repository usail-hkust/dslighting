# DABench Task 298 - 2. Perform a distribution analysis on the "nsamplecov" column. Determine whether the distribution adheres to a normal distribution and calculate the skewness and kurtosis values.

## Task Description

2. Perform a distribution analysis on the "nsamplecov" column. Determine whether the distribution adheres to a normal distribution and calculate the skewness and kurtosis values.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `ts-sc4-wi100000-sl25000-Qrob_Chr05.tree_table.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Test the normality of the data using Shapiro-Wilk Test. Use a significance level (alpha) of 0.05.
Report the p-value associated with the normality test. 
Consider the distribution to be normal if the p-value is larger than 0.05.
Calculate the skewness and kurtosis values.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `298`
- `answer`: `@is_normal[<is_normal>]` where `<is_normal>` is `yes` or `no` according to the normality test.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
