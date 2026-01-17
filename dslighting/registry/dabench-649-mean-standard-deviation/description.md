# DABench Task 649 - 1. Calculate the mean and standard deviation of the X-coordinate column.

## Task Description

1. Calculate the mean and standard deviation of the X-coordinate column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `DES=+2006261.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use built-in Python functions to compute the mean and standard deviation, and round these values to three decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@mean_x[mean] @std_dev_x[standard_deviation]

"mean" and "standard_deviation" are decimal numbers rounded to three decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
