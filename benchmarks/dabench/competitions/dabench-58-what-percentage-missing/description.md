# DABench Task 58 - What is the percentage of missing values in the "No. of cases_min" column? How does this percentage compare to the percentage of missing values in the "No. of deaths_max" column?

## Task Description

What is the percentage of missing values in the "No. of cases_min" column? How does this percentage compare to the percentage of missing values in the "No. of deaths_max" column?

## Concepts

Comprehensive Data Preprocessing, Summary Statistics

## Data Description

Dataset file: `estimated_numbers.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the percentage of missing values for both "No. of cases_min" and "No. of deaths_max" column. Report the exact percentage values.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `58`
- `answer`: two key-value pairs separated by a space: `@percentage_cases_min[<percentage_cases_min>] @percentage_deaths_max[<percentage_deaths_max>]`

Each percentage is between 0 and 100, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
