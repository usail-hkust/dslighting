# DABench Task 62 - Are there any outliers in the "No. of deaths_max" column for each country? How do these outliers affect the overall distribution of recorded deaths?

## Task Description

Are there any outliers in the "No. of deaths_max" column for each country? How do these outliers affect the overall distribution of recorded deaths?

## Concepts

Outlier Detection, Distribution Analysis

## Data Description

Dataset file: `estimated_numbers.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the IQR method (1.5*IQR rule) to detect the outliers. If there are any outliers, remove them and then recalculate the mean number of deaths.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `62`
- `answer`: two key-value pairs separated by a space: `@mean_no_of_deaths_with_outliers[<original_mean>] @mean_no_of_deaths_without_outliers[<new_mean>]`

Means are floats rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
