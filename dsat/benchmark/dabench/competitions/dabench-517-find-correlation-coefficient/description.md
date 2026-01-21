# DABench Task 517 - Find the correlation coefficient between the passenger class and the fare.

## Task Description

Find the correlation coefficient between the passenger class and the fare.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the correlation using the Pearson method. Do not include the rows with null values in either Pclass or Fare in the calculation. Round the final output to 2 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_pclass_fare[correlation_value]

"correlation_value" is a float rounded to 2 decimal places, representing the correlation coefficient between passenger class and fare.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
