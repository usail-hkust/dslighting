# DABench Task 644 - Check if the "Close" column follows a normal distribution.

## Task Description

Check if the "Close" column follows a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `random_stock_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Shapiro-Wilk test to determine whether the "Close" column follows a normal distribution. The null hypothesis is that the data was drawn from a normal distribution. Use a significance level (alpha) of 0.05. If the p-value is less than 0.05, reject the null hypothesis and conclude that the data does not come from a normal distribution. Otherwise, do not reject the null hypothesis and conclude that the data does come from a normal distribution. Round the p-value to four decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@result[result]

"result" is either "Normal distribution" or "Not a normal distribution".

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
