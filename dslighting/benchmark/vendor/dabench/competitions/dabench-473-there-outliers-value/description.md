# DABench Task 473 - Are there any outliers in the "Value" column? If yes, how many and what are their locations (row numbers)?

## Task Description

Are there any outliers in the "Value" column? If yes, how many and what are their locations (row numbers)?

## Concepts

Outlier Detection

## Data Description

Dataset file: `oecd_education_spending.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the IQR method to detect outliers. Define an outlier as a data point that falls below Q1 - 1.5*IQR or above Q3 + 1.5*IQR.
Return the list of row numbers (starting from 0) for those outliers in ascending order. If there are no outliers, return an empty list.
Ignore the null values in the "Value" column.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@outliers[list_of_numbers]

"list_of_numbers" is a list of integers.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
