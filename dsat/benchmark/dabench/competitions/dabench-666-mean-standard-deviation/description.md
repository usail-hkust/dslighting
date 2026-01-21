# DABench Task 666 - Calculate the mean and standard deviation of the MedianHouseValue column in the provided dataset.

## Task Description

Calculate the mean and standard deviation of the MedianHouseValue column in the provided dataset.

## Concepts

Summary Statistics

## Data Description

Dataset file: `my_test_01.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean and standard deviation to four decimal places using built-in Python statistical functions.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@std_dev[std_dev] @mean_value[mean]

"mean" and "std_dev" are values rounded to four decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
