# DABench Task 297 - 1. Is there a significant difference in the mean value of the "nsnps" column between the rows with null values in the "tree" column and the rows without null values in the "tree" column? If yes, what is the p-value of the statistical test?

## Task Description

1. Is there a significant difference in the mean value of the "nsnps" column between the rows with null values in the "tree" column and the rows without null values in the "tree" column? If yes, what is the p-value of the statistical test?

## Concepts

Summary Statistics, Comprehensive Data Preprocessing

## Data Description

Dataset file: `ts-sc4-wi100000-sl25000-Qrob_Chr05.tree_table.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean value for the rows where "tree" is null and the rows where "tree" is not null separately.
Perform an independent two-sample t-test to compare these two groups. Use a significance level (alpha) of 0.05.
Report the p-value associated with the t-test. 
Consider there is a significant difference if the p-value is less than 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `297`
- `answer`: two key-value pairs separated by a space: `@mean_with_tree_notnull[<mean>] @mean_with_tree_null[<mean>]`

Each mean is rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
