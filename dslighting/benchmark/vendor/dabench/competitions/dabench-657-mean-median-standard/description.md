# DABench Task 657 - Calculate the mean, median, and standard deviation of the 'Close' column.

## Task Description

Calculate the mean, median, and standard deviation of the 'Close' column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `YAHOO-BTC_USD_D.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Using pandas library in Python, ignore the missing values, and round the results to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@median_close[median] @std_close[std_deviation] @mean_close[mean]

"mean", "median", and "std_deviation" are decimal numbers rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
