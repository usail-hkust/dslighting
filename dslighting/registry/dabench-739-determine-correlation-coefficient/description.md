# DABench Task 739 - Determine the correlation coefficient between the "Limit" and "Balance" columns in the Credit.csv file.

## Task Description

Determine the correlation coefficient between the "Limit" and "Balance" columns in the Credit.csv file.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `Credit.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient to represent the correlation. Round the result to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_coefficient[correlation_value]

where "correlation_value" is the calculated Pearson correlation coefficient between "Limit" and "Balance", rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
