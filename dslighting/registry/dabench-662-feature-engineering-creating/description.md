# DABench Task 662 - Perform feature engineering by creating a new column called 'Price Change' that represents the difference between the 'Close' and 'Open' prices for each day. Calculate the median and standard deviation of the 'Price Change' column.

## Task Description

Perform feature engineering by creating a new column called 'Price Change' that represents the difference between the 'Close' and 'Open' prices for each day. Calculate the median and standard deviation of the 'Price Change' column.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `YAHOO-BTC_USD_D.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Create the 'Price Change' column by subtracting the 'Open' column from the 'Close' column for each observation. Calculate the median and standard deviation by using the corresponding functions in Python's 'statistics' module.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@stddev_price_change[stddev_price_change] @median_price_change[median_price_change]

"median_price_change" is the median of the 'Price Change' column, rounded to two decimal places. "stddev_price_change" is the standard deviation of the 'Price Change' column, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
