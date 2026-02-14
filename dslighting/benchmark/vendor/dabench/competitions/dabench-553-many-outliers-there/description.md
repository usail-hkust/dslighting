# DABench Task 553 - How many outliers are there in the TPH_PLT column?

## Task Description

How many outliers are there in the TPH_PLT column?

## Concepts

Outlier Detection

## Data Description

Dataset file: `tree.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Detect outliers in the 'TPH_PLT' column using the IQR method, where observations that fall below Q1 - 1.5*IQR or above Q3 + 1.5*IQR are considered outliers. Do not consider missing values, as it was stated there are no missing values in this column.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `553`
- `answer`: `@outliers_count[<count>]` where `<count>` is a non-negative integer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
