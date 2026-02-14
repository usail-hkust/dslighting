# DABench Task 272 - Create a new feature named "TOTUSJZ_TOTUSJH_RATIO" by dividing the TOTUSJZ column by the TOTUSJH column. Calculate the mean and standard deviation of this new feature.

## Task Description

Create a new feature named "TOTUSJZ_TOTUSJH_RATIO" by dividing the TOTUSJZ column by the TOTUSJH column. Calculate the mean and standard deviation of this new feature.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `3901.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Add a small constant (1e-10) to the denominator (TOTUSJH column) to avoid dividing by zero.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `272`
- `answer`: two key-value pairs separated by a space: `@mean_ratio[<value>] @stddev_ratio[<value>]`

Both values are rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
