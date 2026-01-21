# DABench Task 132 - Identify and count the number of outliers in the fare paid by passengers using the Z-score method.

## Task Description

Identify and count the number of outliers in the fare paid by passengers using the Z-score method.

## Concepts

Outlier Detection

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Calculate the Z-score for each fare using the mean and standard deviation of the fare data.
Determine an outlier to be any fare with a Z-score greater than 3 or less than -3.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `132`
- `answer`: `@outlier_count[<count>]` where `<count>` is the integer number of outliers.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
