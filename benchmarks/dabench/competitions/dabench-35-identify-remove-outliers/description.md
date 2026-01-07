# DABench Task 35 - Identify and remove any outliers in the "row retention time" column using the Z-score method with a Z-score threshold of 3. Provide the number of removed outliers.

## Task Description

Identify and remove any outliers in the "row retention time" column using the Z-score method with a Z-score threshold of 3. Provide the number of removed outliers.

## Concepts

Outlier Detection, Comprehensive Data Preprocessing

## Data Description

Dataset file: `imp.score.ldlr.metabolome.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use the Z-score method to identify outliers in the "row retention time" column. Any data point with a Z-score greater than 3 or less than -3 is considered an outlier and should be removed.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `35`
- `answer`: `@removed_outliers_count[<count>]` where `<count>` is a non-negative integer.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
