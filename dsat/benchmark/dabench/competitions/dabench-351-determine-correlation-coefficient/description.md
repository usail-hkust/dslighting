# DABench Task 351 - Determine the correlation coefficient between Age and Fare.

## Task Description

Determine the correlation coefficient between Age and Fare.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `test_x.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient between 'Age' and 'Fare'. Use pandas.DataFrame.corr method with the 'pearson' method. Ignore NA/null values.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `351`
- `answer`: `@correlation_coefficient[<correlation_coefficient>]` where `<correlation_coefficient>` is a float rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
