# DABench Task 349 - Calculate the mean age of the passengers.

## Task Description

Calculate the mean age of the passengers.

## Concepts

Summary Statistics

## Data Description

Dataset file: `test_x.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

The mean should be calculated on the full 'Age' column with no filtering. Use the default parameter values for pandas.DataFrame.mean method; in particular, ignore NA/null values and compute the arithmetic mean along the specified axis.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `349`
- `answer`: `@mean_age[<mean_age>]` where `<mean_age>` is the calculated mean age (two decimals).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
