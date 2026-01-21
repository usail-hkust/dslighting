# DABench Task 179 - Calculate the Pearson correlation coefficient between the age and fare variables for passengers who survived and were in first class.

## Task Description

Calculate the Pearson correlation coefficient between the age and fare variables for passengers who survived and were in first class.

## Concepts

Summary Statistics, Correlation Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use only passengers that survived and were in the first class. Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between age and fare.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `179`
- `answer`: `@correlation_coefficient[<c_value>]` where `<c_value>` is between -1 and 1, rounded to three decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
