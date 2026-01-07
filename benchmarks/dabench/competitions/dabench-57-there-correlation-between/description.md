# DABench Task 57 - Is there a correlation between the number of cases and the number of deaths recorded?

## Task Description

Is there a correlation between the number of cases and the number of deaths recorded?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `estimated_numbers.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between number of cases and number of deaths. Convert the data types of 'No. of cases' and 'No. of deaths' column from Object (String) to Int64 before performing calculations. Do this for complete data rather than specific country or year.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `57`
- `answer`: `@correlation_coefficient[<r_value>]` where `<r_value>` is between -1 and 1, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
