# DABench Task 716 - 1. Perform data preprocessing by dropping the rows where the "Wins" in the "JAMES LOGAN" column is missing, and calculate the mean and standard deviation of the remaining "Wins" values.

## Task Description

1. Perform data preprocessing by dropping the rows where the "Wins" in the "JAMES LOGAN" column is missing, and calculate the mean and standard deviation of the remaining "Wins" values.

## Concepts

Summary Statistics, Comprehensive Data Preprocessing

## Data Description

Dataset file: `Current_Logan.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Exclude rows where "Wins" is missing or is a non-numeric value.
Convert "Wins" to numeric values before calculations.
Compute the mean and standard deviation to two decimal places.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@stddev_wins[stddev_wins]

"stddev_wins" is a numeric value rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
