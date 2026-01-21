# DABench Task 25 - Check if the distribution of BMI values in the dataset follows a normal distribution.

## Task Description

Check if the distribution of BMI values in the dataset follows a normal distribution.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `insurance.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Consider the distribution as normal if the absolute value of skewness is less than 0.5. Calculate skewness using Python's built-in function.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `25`
- `answer`: `@bmi_distribution[<status>]` where `<status>` is `normal` or `not_normal` per the constraints.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
