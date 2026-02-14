# DABench Task 116 - Are there any outliers in the happiness scores of countries? If so, which countries are considered outliers?

## Task Description

Are there any outliers in the happiness scores of countries? If so, which countries are considered outliers?

## Concepts

Outlier Detection

## Data Description

Dataset file: `2015.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Outliers should be determined by the Z-score method. If a country has a Z score greater than 3 or less than -3, it is considered an outlier. The calculation should be done using the population standard deviation formula.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `116`
- `answer`: `@outlier_countries[<country1,country2,...>]` a comma-separated list of outlier countries (empty if none).

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
