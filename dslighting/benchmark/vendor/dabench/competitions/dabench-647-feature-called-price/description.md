# DABench Task 647 - Create a new feature called "Price Range" by calculating the difference between the "High" and "Low" values for each entry. Then, determine if the "Price Range" follows a normal distribution.

## Task Description

Create a new feature called "Price Range" by calculating the difference between the "High" and "Low" values for each entry. Then, determine if the "Price Range" follows a normal distribution.

## Concepts

Feature Engineering, Distribution Analysis

## Data Description

Dataset file: `random_stock_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate "Price Range" for each row by subtracting the "Low" value from the "High" value. Test the normality of the resulting column using the Shapiro-Wilk test. Consider the data to follow a normal distribution if the p-value is greater than 0.05.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@price_range_mean[mean_value] @is_normal[str] @price_range_stddev[stddev_value]

"mean_value" and "stddev_value" are the mean and standard deviation of "Price Range", rounded to two decimal places. "str" is "yes" or "no" based on the Shapiro-Wilk test result.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
