# DABench Task 643 - Calculate the mean, standard deviation, minimum, and maximum values of the "Volume" column.

## Task Description

Calculate the mean, standard deviation, minimum, and maximum values of the "Volume" column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `random_stock_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use Python's built-in statistical functions to calculate these values. Round these numbers to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@std_volume[standard_deviation_value] @min_volume[minimum_value] @max_volume[maximum_value] @mean_volume[mean_value]

All values are numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
