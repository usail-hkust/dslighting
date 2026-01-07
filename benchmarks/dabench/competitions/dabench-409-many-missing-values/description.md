# DABench Task 409 - How many missing values are there in the "Cabin" column?

## Task Description

How many missing values are there in the "Cabin" column?

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Count the number of missing values in the 'Cabin' column in the dataset. Treat null values as missing values.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@missing_values[missing_values]

"missing_values" is an integer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
