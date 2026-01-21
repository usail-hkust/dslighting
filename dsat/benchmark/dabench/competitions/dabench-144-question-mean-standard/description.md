# DABench Task 144 - Question 1: Calculate the mean and standard deviation of the percentage of votes received by the Democratic and Republican parties. Then, determine if the distribution of the percentage of votes follows a normal distribution using Anderson-Darling test with the significance level (alpha) of 0.05.

## Task Description

Question 1: Calculate the mean and standard deviation of the percentage of votes received by the Democratic and Republican parties. Then, determine if the distribution of the percentage of votes follows a normal distribution using Anderson-Darling test with the significance level (alpha) of 0.05.

## Concepts

Summary Statistics, Distribution Analysis

## Data Description

Dataset file: `election2016.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

The desired calculation of the mean should be rounded up to 2 decimal places and the standard deviation should be rounded up to 3 decimal places.
Use Anderson-Darling test to assess the normalcy of the distribution and if the p-value obtained is less than 0.05, then the distribution can be considered as 'Not Normal' else 'Normal'.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `144`
- `answer`: four key-value pairs separated by spaces: `@std_dev_dem[<std_dev_dem>] @mean_dem[<mean_dem>] @std_dev_gop[<std_dev_gop>] @mean_gop[<mean_gop>]`

`mean_dem`/`mean_gop` rounded to two decimals; `std_dev_dem`/`std_dev_gop` rounded to three decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
