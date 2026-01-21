# DABench Task 176 - Calculate the median age of male passengers who survived and paid a fare greater than the average fare. Calulate only the ages that are not null.

## Task Description

Calculate the median age of male passengers who survived and paid a fare greater than the average fare. Calulate only the ages that are not null.

## Concepts

Summary Statistics, Correlation Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
All null values in the "Age" column are not considered in the calculation.
The passengers considered for this question should meet all the following conditions: they are male; they survived; their fare is greater than the average fare.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `176`
- `answer`: `@median_age[<median_age>]` where the value is rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
