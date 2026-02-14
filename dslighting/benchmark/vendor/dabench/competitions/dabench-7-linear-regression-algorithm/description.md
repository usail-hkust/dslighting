# DABench Task 7 - Apply the linear regression algorithm from the sklearn library to predict whether a passenger survived or not based on the features 'Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', and 'Embarked'. Encode 'Sex' and 'Embarked' to numerical values before applying the model. Split the dataset into a training set (80%) and a testing set (20%), train the model on the training set, and evaluate its performance on the testing set using the accuracy score. Ensure that the train_test_split function's random_state parameter is set to 42 for consistency.

## Task Description

Apply the linear regression algorithm from the sklearn library to predict whether a passenger survived or not based on the features 'Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', and 'Embarked'. Encode 'Sex' and 'Embarked' to numerical values before applying the model. Split the dataset into a training set (80%) and a testing set (20%), train the model on the training set, and evaluate its performance on the testing set using the accuracy score. Ensure that the train_test_split function's random_state parameter is set to 42 for consistency.

## Concepts

Machine Learning

## Data Description

Dataset file: `test_ave.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Use one-hot encoding for the 'Sex' and 'Embarked' features. Use the "linear regression" model provided by the sklearn library in Python.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `7`
- `answer`: `@prediction_accuracy[<accuracy>]` where `<accuracy>` is between 0.0 and 1.0, rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
