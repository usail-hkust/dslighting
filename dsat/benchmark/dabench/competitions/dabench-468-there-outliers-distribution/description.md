# DABench Task 468 - 2. Are there any outliers in the age distribution of offenders in 'Assault' category, according to the IQR method? If yes, report the number of outliers.

## Task Description

2. Are there any outliers in the age distribution of offenders in 'Assault' category, according to the IQR method? If yes, report the number of outliers.

## Concepts

Distribution Analysis, Outlier Detection

## Data Description

Dataset file: `arrest_expungibility.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

You are to use the Interquartile Range (IQR) method for outlier detection. Calculate the IQR as Q3 (75th percentile) - Q1 (25th percentile) for the 'Assault' category. Outliers are considered as values lying below Q1 - 1.5 * IQR or above Q3 + 1.5 * IQR.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@number_of_outliers[number]

"number" is a positive integer denoting the number of outliers.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
