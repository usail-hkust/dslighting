# DABench Task 520 - Create a new feature called 'FamilySize' by combining the 'SibSp' and 'Parch' columns, which represents the total number of family members a passenger had aboard the Titanic. Then, find the correlation coefficient between 'FamilySize' and 'Survived'.

## Task Description

Create a new feature called 'FamilySize' by combining the 'SibSp' and 'Parch' columns, which represents the total number of family members a passenger had aboard the Titanic. Then, find the correlation coefficient between 'FamilySize' and 'Survived'.

## Concepts

Feature Engineering, Correlation Analysis

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Create 'FamilySize' by adding up 'SibSp' and 'Parch', then calculate the Pearson correlation coefficient between 'FamilySize' and 'Survived'.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@correlation_coefficient[number]

"number" is the Pearson correlation coefficient between 'FamilySize' and 'Survived', rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Medium
