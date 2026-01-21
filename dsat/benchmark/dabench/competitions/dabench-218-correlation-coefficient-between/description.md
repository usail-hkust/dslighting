# DABench Task 218 - Calculate the correlation coefficient between the positive_diffsel and negative_diffsel columns.

## Task Description

Calculate the correlation coefficient between the positive_diffsel and negative_diffsel columns.

## Concepts

Correlation Analysis

## Data Description

Dataset file: `ferret-Pitt-2-preinf-lib2-100_sitediffsel.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Calculate the Pearson correlation coefficient (r) to assess the strength of the linear relationship between positive_diffsel and negative_diffsel. 
Do not remove any outliers or modify the data prior to computation. 
Use all available data points for the computation of the correlation coefficient.}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `218`
- `answer`: `@correlation_coefficient[<r_value>]` where `<r_value>` is between -1 and 1, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
