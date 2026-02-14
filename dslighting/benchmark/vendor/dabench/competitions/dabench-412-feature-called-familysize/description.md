# DABench Task 412 - Create a new feature called "FamilySize" by adding the "SibSp" and "Parch" columns together. What is the mean "FamilySize" for passengers who survived versus passengers who did not survive?

## Task Description

Create a new feature called "FamilySize" by adding the "SibSp" and "Parch" columns together. What is the mean "FamilySize" for passengers who survived versus passengers who did not survive?

## Concepts

Feature Engineering

## Data Description

Dataset file: `titanic_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Calculate the mean of "FamilySize" separately for the passengers who survived and the passengers who did not survive. "FamilySize" should be an integer value. The mean should be calculated rounding up to two decimal places.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include both markers (space or newline separated) in this order (quote the cell as in the sample to preserve spaces/newlines):
@mean_familysize_survived[answer1] @mean_familysize_did_not_survive[answer2]

"answer1" is the mean "FamilySize" for passengers who survived and "answer2" is the mean "FamilySize" for passengers who did not survive. Both results should be rounded to 2 decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
