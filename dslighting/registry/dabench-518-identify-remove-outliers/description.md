# DABench Task 518 - Identify and remove any outliers in the fare column using the Z-score method.

## Task Description

Identify and remove any outliers in the fare column using the Z-score method.

## Concepts

Outlier Detection

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Z-scores for the 'Fare' column values and classify a value as an outlier if its Z-score is greater than 3. After removal of outliers, calculate the number of entries left in the dataset.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@number_of_entries_left[number]

"number" is the total number of entries left in the dataset after removal of outliers.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
