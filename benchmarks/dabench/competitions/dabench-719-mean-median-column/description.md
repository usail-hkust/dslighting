# DABench Task 719 - 1. Calculate the mean and median of the 'mpg' column.

## Task Description

1. Calculate the mean and median of the 'mpg' column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `auto-mpg.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean and median of the 'mpg' column without excluding any data. Round your results to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@median_mpg[median_value] @mean_mpg[mean_value]

'mean_value' and 'median_value' are numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
