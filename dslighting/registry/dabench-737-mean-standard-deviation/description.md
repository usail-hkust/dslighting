# DABench Task 737 - Calculate the mean and standard deviation of the "Income" column in the Credit.csv file.

## Task Description

Calculate the mean and standard deviation of the "Income" column in the Credit.csv file.

## Concepts

Summary Statistics

## Data Description

Dataset file: `Credit.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean and standard deviation using built-in functions in Python's pandas library. Round the outputs to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@mean_income[mean_value] @std_dev_income[std_dev_value]

"mean_value" and "std_dev_value" are the calculated mean and standard deviation of the "Income" column, respectively. Both should be rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
