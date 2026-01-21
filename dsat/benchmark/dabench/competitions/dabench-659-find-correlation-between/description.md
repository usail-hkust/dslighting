# DABench Task 659 - Find the correlation between the 'High' and 'Low' columns.

## Task Description

Find the correlation between the 'High' and 'Low' columns.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `YAHOO-BTC_USD_D.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient, ignore the missing values, and round the result to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_high_low[correlation]

"correlation" is a decimal number between -1 and 1, representing the Pearson correlation coefficient between 'High' and 'Low' columns, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
