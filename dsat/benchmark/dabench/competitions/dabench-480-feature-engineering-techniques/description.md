# DABench Task 480 - Apply feature engineering techniques to the dataset. Create a new feature by subtracting the mean value of the "Value" column from each value in that column. Calculate and report the standard deviation of this new feature.

## Task Description

Apply feature engineering techniques to the dataset. Create a new feature by subtracting the mean value of the "Value" column from each value in that column. Calculate and report the standard deviation of this new feature.

## Concepts

Feature Engineering, Summary Statistics

## Data Description

Dataset file: `oecd_education_spending.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Create a new feature by subtracting the mean value of the "Value" column from each value in that column. Calculate the standard deviation of the new feature.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@standard_deviation[std_value]

"std_value" is a positive number rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
