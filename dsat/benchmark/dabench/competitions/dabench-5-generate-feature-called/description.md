# DABench Task 5 - Generate a new feature called "FamilySize" by summing the "SibSp" and "Parch" columns. Then, calculate the Pearson correlation coefficient (r) between the "FamilySize" and "Fare" columns.

## Task Description

Generate a new feature called "FamilySize" by summing the "SibSp" and "Parch" columns. Then, calculate the Pearson correlation coefficient (r) between the "FamilySize" and "Fare" columns.

## Concepts

Feature Engineering, Correlation Analysis

## Data Description

Dataset file: `test_ave.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Create a new column 'FamilySize' that is the sum of 'SibSp' and 'Parch' for each row.
Calculate the Pearson correlation coefficient between 'FamilySize' and 'Fare'
Do not perform any further data cleaning or preprocessing steps before calculating the correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `5`
- `answer`: `@correlation_coefficient[<r_value>]` where `<r_value>` is the Pearson correlation between 'FamilySize' and 'Fare' (two decimals, between -1 and 1).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
