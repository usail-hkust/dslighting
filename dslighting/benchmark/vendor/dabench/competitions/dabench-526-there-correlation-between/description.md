# DABench Task 526 - Is there a correlation between the passenger class and the fare paid?

## Task Description

Is there a correlation between the passenger class and the fare paid?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `titanic_test.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient (r) to assess the strength and direction of the linear relationship between 'Pclass' and 'Fare'. Ignore rows with missing values in these two columns. Round the result to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `526`
- `answer`: `@correlation_coefficient[<r_value>]` where `<r_value>` is a number between -1 and 1 (two decimals). Example: `@correlation_coefficient[-0.55]`.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
