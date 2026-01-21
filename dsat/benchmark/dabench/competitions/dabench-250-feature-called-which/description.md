# DABench Task 250 - Create a new feature called "batting_average_minus_on_base_percentage" which represents the difference between a player's batting average and their on-base percentage. Calculate the mean and standard deviation of this new feature.

## Task Description

Create a new feature called "batting_average_minus_on_base_percentage" which represents the difference between a player's batting average and their on-base percentage. Calculate the mean and standard deviation of this new feature.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `baseball_data.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

To calculate the new feature, subtract each player's on-base percentage from their batting average. Ignore the missing values and areas with null values for batting average or on-base percentage. Calculate both the mean and standard deviation using these new feature values.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `250`
- `answer`: two key-value pairs separated by a space: `@mean[<mean_value>] @std_dev[<std_dev_value>]`

Both values are rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
