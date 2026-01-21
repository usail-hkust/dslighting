# DABench Task 216 - Calculate the mean and standard deviation of the abs_diffsel column.

## Task Description

Calculate the mean and standard deviation of the abs_diffsel column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `ferret-Pitt-2-preinf-lib2-100_sitediffsel.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
The mean and standard deviation should be calculated directly from the 'abs_diffsel' column.
Do not remove any outliers or modify the data prior to calculation.
The mean and standard deviation should be computed directly from all available data points.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `216`
- `answer`: two key-value pairs separated by a space: `@std_dev[<std_dev_value>] @mean[<mean_value>]`

Both values are positive floats rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
