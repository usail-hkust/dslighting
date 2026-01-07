# DABench Task 24 - Calculate the mean age of the individuals in the dataset.

## Task Description

Calculate the mean age of the individuals in the dataset.

## Concepts

Summary Statistics

## Data Description

Dataset file: `insurance.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Ignore rows with missing values in the age column. Use Python's built-in function to calculate the mean.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `24`
- `answer`: `@mean_age[<value>]` where `<value>` is between 0 and 100, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
