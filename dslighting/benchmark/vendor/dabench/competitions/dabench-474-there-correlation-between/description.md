# DABench Task 474 - Is there a correlation between the "Value" column and the "TIME" column? If yes, what is the correlation coefficient?

## Task Description

Is there a correlation between the "Value" column and the "TIME" column? If yes, what is the correlation coefficient?

## Concepts

Correlation Analysis

## Data Description

Dataset file: `oecd_education_spending.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the Pearson correlation coefficient.
Ignore all the pairs that either "Value" or "TIME" is null.
Round your final answer to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_coefficient[number]

"number" is a floating-point number between -1 and 1, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Easy
