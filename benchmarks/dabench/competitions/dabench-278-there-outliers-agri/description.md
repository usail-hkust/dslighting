# DABench Task 278 - Are there any outliers in the Agri column of the dataset? If yes, how would you detect them using Z-scores?

## Task Description

Are there any outliers in the Agri column of the dataset? If yes, how would you detect them using Z-scores?

## Concepts

Outlier Detection

## Data Description

Dataset file: `veracruz 2016.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Z-scores for the Agri column values. Any data point that has a Z-score greater than 3 or less than -3 should be considered as an outlier.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `278`
- `answer`: `@outliers_count[<outliers_value>]` where `<outliers_value>` is the non-negative integer count of outliers detected using Z-score.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
