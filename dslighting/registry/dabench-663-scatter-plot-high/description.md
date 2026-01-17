# DABench Task 663 - Create a scatter plot of the 'High' and 'Low' columns to visualize the relationship between the highest and lowest prices for each day. Calculate the Pearson correlation coefficient between these two columns.

## Task Description

Create a scatter plot of the 'High' and 'Low' columns to visualize the relationship between the highest and lowest prices for each day. Calculate the Pearson correlation coefficient between these two columns.

## Concepts

Distribution Analysis, Correlation Analysis

## Data Description

Dataset file: `YAHOO-BTC_USD_D.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Constraints:
1. Use the Pearson method to calculate the correlation coefficient.
2. Round the correlation coefficient to two decimal places.
3. Do not consider any missing values in the data while calculating the correlation.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_coefficient[correlation_value]

"correlation_value" is a number between -1 and 1, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
