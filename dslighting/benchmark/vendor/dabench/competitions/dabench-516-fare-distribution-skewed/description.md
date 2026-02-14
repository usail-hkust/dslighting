# DABench Task 516 - Check if the fare distribution is skewed.

## Task Description

Check if the fare distribution is skewed.

## Concepts

Distribution Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the skewness of the fare column using Pearson's moment coefficient of skewness. Ignore null values. Round the final output to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@skewness_fare[skewness_value]

"skewness_value" is a float rounded to 2 decimal places, representing the skewness of the fare distribution.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
