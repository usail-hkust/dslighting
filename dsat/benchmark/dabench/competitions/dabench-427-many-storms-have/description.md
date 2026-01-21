# DABench Task 427 - 3. How many storms have null values in the "min_p" column?

## Task Description

3. How many storms have null values in the "min_p" column?

## Concepts

Comprehensive Data Preprocessing

## Data Description

Dataset file: `cost_data_with_errors.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Count the number of entries which have the null value in the "min_p" column. Only the null values should be counted, and not any irrelevant or erroneous data that might be present.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@null_entries_count[number]

"number" is an integer indicating the count of null entries in the "min_p" column.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
