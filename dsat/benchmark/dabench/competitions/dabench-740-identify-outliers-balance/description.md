# DABench Task 740 - Identify any outliers in the "Balance" column of the Credit.csv file using the Z-score method.

## Task Description

Identify any outliers in the "Balance" column of the Credit.csv file using the Z-score method.

## Concepts

Outlier Detection, Comprehensive Data Preprocessing

## Data Description

Dataset file: `Credit.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Define an outlier to be any data point that falls more than 3 standard deviations from the mean. Use the formula Z = (X - μ) / σ where X is a data point, μ is the mean, and σ is the standard deviation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@outliers[outliers_count]

where "outliers_count" is an integer indicating the total number of outliers identified.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
