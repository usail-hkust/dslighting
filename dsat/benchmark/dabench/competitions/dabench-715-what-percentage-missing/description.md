# DABench Task 715 - 3. What is the percentage of missing values in the "Unnamed: 8" column?

## Task Description

3. What is the percentage of missing values in the "Unnamed: 8" column?

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `Current_Logan.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

The missing values are represented as NaN in pandas dataframe.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@missing_percentage[percentage]

where "percentage" is a number between 0 and 100, representing the percentage of missing values in the column, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
