# DABench Task 26 - Calculate the correlation coefficient between the charges incurred by individuals and the number of children they have.

## Task Description

Calculate the correlation coefficient between the charges incurred by individuals and the number of children they have.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `insurance.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Ignore rows with missing values in charges and children columns. Calculate the Pearson correlation coefficient.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `26`
- `answer`: `@correlation_coefficient[<value>]` where `<value>` is between -1 and 1, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
