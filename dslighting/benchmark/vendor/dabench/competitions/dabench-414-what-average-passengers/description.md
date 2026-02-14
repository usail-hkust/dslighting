# DABench Task 414 - What is the average age of passengers in each ticket class (Pclass)?

## Task Description

What is the average age of passengers in each ticket class (Pclass)?

## Concepts

Summary Statistics, Comprehensive Data Preprocessing

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the average (mean) age of the passengers in each class separately (Pclass = 1, Pclass = 2, Pclass = 3).
Ignore the rows with missing age.
Round the average age to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include all markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@first_class_average_age[average_age_1] @second_class_average_age[average_age_2] @third_class_average_age[average_age_3]

"average_age_1/2/3" are the average ages for classes 1/2/3, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
