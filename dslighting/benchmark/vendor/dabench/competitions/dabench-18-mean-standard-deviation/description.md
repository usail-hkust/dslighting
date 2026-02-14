# DABench Task 18 - Calculate the mean and standard deviation of the "Mar.2019" column.

## Task Description

Calculate the mean and standard deviation of the "Mar.2019" column.

## Concepts

Summary Statistics

## Data Description

Dataset file: `unemployement_industry.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Outliers are to be pruned via the interquartile range method before calculating the mean and standard deviation. Handle missing values by using listwise deletion method. Report the measures rounded to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `18`
- `answer`: `@mean_mar_2019[<mean>] @sd_mar_2019[<sd>]` where both are numbers rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
