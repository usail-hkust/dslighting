# DABench Task 725 - 1. Investigate the relationship between 'displacement' and 'mpg' by analyzing the distribution of 'mpg' for each unique value of 'displacement'. Calculate the mean and median 'mpg' for each of the three most common unique values of 'displacement'.

## Task Description

1. Investigate the relationship between 'displacement' and 'mpg' by analyzing the distribution of 'mpg' for each unique value of 'displacement'. Calculate the mean and median 'mpg' for each of the three most common unique values of 'displacement'.

## Concepts

Distribution Analysis, Correlation Analysis

## Data Description

Dataset file: `auto-mpg.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
- Only consider the three unique 'displacement' values that occur most frequently in the dataset.
- The 'mpg' means and medians must be calculated for each of these three values separately, with 'mpg' values only from rows with the corresponding 'displacement' value.
- Results must be rounded to two decimal places.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@median1[median1] @mean1[mean1]

"median1" and "mean1" are the median and mean 'mpg' values (rounded to two decimals) for the relevant 'displacement' group.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
