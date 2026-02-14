# DABench Task 27 - Identify the outliers in the charges incurred by individuals using the Z-score method.

## Task Description

Identify the outliers in the charges incurred by individuals using the Z-score method.

## Concepts

Outlier Detection

## Data Description

Dataset file: `insurance.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Apply the Z-score method for outlier detection using the 1.5xIQR rule. Consider any value that falls below Q1 - 1.5 * IQR or above Q3 + 1.5 * IQR as an outlier. Report the total number of outliers, and the mean and median charges of these identified outliers.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `27`
- `answer`: three key-value pairs separated by spaces: `@median_charges_outliers[<value>] @mean_charges_outliers[<value>] @total_outliers[<count>]`

Counts are integers; charges values are floats rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
