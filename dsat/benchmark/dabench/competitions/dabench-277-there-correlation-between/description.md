# DABench Task 277 - Is there any correlation between the MedInd and LarInd columns in the given dataset? If yes, what is the correlation coefficient?

## Task Description

Is there any correlation between the MedInd and LarInd columns in the given dataset? If yes, what is the correlation coefficient?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `veracruz 2016.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson's correlation coefficient (r), a statistical measure that calculates the strength of the relationship between the relative movements of two variables, between the MedInd and LarInd columns. The Pearson's correlation coefficient should be rounded to 4 decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `277`
- `answer`: `@correlation_coefficient[<correlation_value>]` where `<correlation_value>` is between -1 and 1 (four decimals).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
