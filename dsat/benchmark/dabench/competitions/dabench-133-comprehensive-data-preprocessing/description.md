# DABench Task 133 - Perform comprehensive data preprocessing for the dataset by handling missing values in the age and cabin columns. Use the deletion strategy for the missing values in the cabin column and imputation strategy for the missing values in the age column.

## Task Description

Perform comprehensive data preprocessing for the dataset by handling missing values in the age and cabin columns. Use the deletion strategy for the missing values in the cabin column and imputation strategy for the missing values in the age column.

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
For the deletion strategy in the cabin column, remove any row that has a missing value in the cabin column.
For the imputation strategy in the age column, replace the missing values with the median age of all passengers.
Report on the new total number of rows after deletion and the median age used for imputation.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `133`
- `answer`: two key-value pairs separated by a space: `@median_age[<value>] @row_count[<count>]`

`count` is a positive integer after deletion; `value` is the median age (one decimal).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
