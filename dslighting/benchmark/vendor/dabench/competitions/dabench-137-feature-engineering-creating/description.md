# DABench Task 137 - Perform feature engineering by creating a new binary feature called "IsAlone" that indicates whether a passenger is traveling alone or with family. Use the "SibSp" and "Parch" columns to determine if a passenger has any accompanying family members. Then, train a logistic regression machine learning model using the new feature and the Survival rate as the output variable.

## Task Description

Perform feature engineering by creating a new binary feature called "IsAlone" that indicates whether a passenger is traveling alone or with family. Use the "SibSp" and "Parch" columns to determine if a passenger has any accompanying family members. Then, train a logistic regression machine learning model using the new feature and the Survival rate as the output variable.

## Concepts

Feature Engineering, Machine Learning

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

The logistic regression model should be implemented with scikit-learn’s LogisticRegression with default parameters. Use the 'IsAlone' feature and 'Survived' as the output variable. The model should be trained using a 70:30 train-test split, balancing the class weights. Use a random seed of 42 for reproducibility.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `137`
- `answer`: `@model_score[<model_accuracy>]` where `<model_accuracy>` is between 0 and 1, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
