# DABench Task 175 - Identify if there are any outliers in the age of the passengers on the Titanic using the Z-score method. Use a threshold of 3 for outlier detection.

## Task Description

Identify if there are any outliers in the age of the passengers on the Titanic using the Z-score method. Use a threshold of 3 for outlier detection.

## Concepts

Outlier Detection

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use Z-score method for outlier detection. Any data point that has a Z-score greater than 3 or less than -3 should be considered an outlier. The python library scipy's zscore() function should be used. Ignore the null values during calculation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `175`
- `answer`: `@outliers_count[<outliers_count>]` where the value is an integer count of outliers.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
