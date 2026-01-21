# DABench Task 741 - Create a new feature in the Credit.csv file by calculating the ratio of "Balance" to "Limit" for each individual.

## Task Description

Create a new feature in the Credit.csv file by calculating the ratio of "Balance" to "Limit" for each individual.

## Concepts

Feature Engineering, Comprehensive Data Preprocessing

## Data Description

Dataset file: `Credit.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the ratio as Balance / Limit. For any individual with a Limit of zero, their ratio should be defined as zero to avoid division by zero.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@addedfeature[ratio]

"ratio" refers to the newly created column containing the ratio of balance to limit for each individual, with a precision of two decimal places for each individual's ratio data.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
