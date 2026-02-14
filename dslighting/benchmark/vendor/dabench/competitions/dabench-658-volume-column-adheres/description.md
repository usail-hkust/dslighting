# DABench Task 658 - Check if the 'Volume' column adheres to a normal distribution.

## Task Description

Check if the 'Volume' column adheres to a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `YAHOO-BTC_USD_D.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Using numpy and scipy libraries in Python, ignore the missing values, perform a Kolmogorov-Smirnov test with a significance level (alpha) of 0.05 where if the p-value is less than 0.05, the 'Volume' does not adhere to normal distribution. If the p-value is greater than or equal to 0.05, the 'Volume' adheres to normal distribution.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@result_ks_test[result]

"result" is a string that can either be "normal" or "not_normal" based on the conditions specified in the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
