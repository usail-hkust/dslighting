# DABench Task 324 - Are there any missing values in the dataset? If so, which column has the highest number of missing values?

## Task Description

Are there any missing values in the dataset? If so, which column has the highest number of missing values?

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `0020200722.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Columns with missing values: HOMEDESCRIPTION, NEUTRALDESCRIPTION, VISITORDESCRIPTION, SCORE, SCOREMARGIN.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `324`
- `answer`: `@max_missing_values[<column_name>]` containing the name of the column with the highest number of missing values.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
