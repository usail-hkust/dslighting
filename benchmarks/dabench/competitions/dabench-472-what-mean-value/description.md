# DABench Task 472 - What is the mean value of the "Value" column?

## Task Description

What is the mean value of the "Value" column?

## Concepts

Summary Statistics

## Data Description

Dataset file: `oecd_education_spending.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Ignore all the null values in the "Value" column.
Round your final answer to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@mean_value[number]

"number" is a floating-point number rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
