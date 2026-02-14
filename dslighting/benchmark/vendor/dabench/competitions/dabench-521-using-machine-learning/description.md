# DABench Task 521 - Using machine learning algorithms, build a classification model to predict survival (0 = No, 1 = Yes) based on the passenger's age, gender, and fare. Train a logistic regression model with default parameters provided by the sklearn library. Evaluate the model's performance using accuracy as the evaluation metric.

## Task Description

Using machine learning algorithms, build a classification model to predict survival (0 = No, 1 = Yes) based on the passenger's age, gender, and fare. Train a logistic regression model with default parameters provided by the sklearn library. Evaluate the model's performance using accuracy as the evaluation metric.

## Concepts

Machine Learning, Feature Engineering

## Data Description

Dataset file: `titanic.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Split the dataset into a training set and a test set with a ratio of 70:30 using sklearn's train_test_split function with a random_state of 42. Don't balance the classes or perform any other preprocessing that isn't mentioned.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@classifier_accuracy[Accuracy Score]

"Accuracy Score" is a float between 0 and 1, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
