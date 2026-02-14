# DABench Task 9 - Calculate the mean value of the "Close Price" column.

## Task Description

Calculate the mean value of the "Close Price" column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `GODREJIND.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the built-in Python (numpy or pandas) to calculate the mean. Do not use any pre-built packages or libraries for mean calculation other than numpy or pandas. The calculation should be done on the whole "Close Price" column. Values in this column should not be rounded or changed in any way before the calculation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `9`
- `answer`: `@mean_close_price[<mean_value>]` where `<mean_value>` is a float rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
