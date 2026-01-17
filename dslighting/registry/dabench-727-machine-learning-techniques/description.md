# DABench Task 727 - 3. Use machine learning techniques to predict the 'mpg' of a vehicle based on its 'weight' and 'acceleration' features. Split the dataset into a training set and a testing set with the ratio of size 8:2. Train a linear regression model on the training set and evaluate its performance by calculating the mean squared error (MSE) on the testing set.

## Task Description

3. Use machine learning techniques to predict the 'mpg' of a vehicle based on its 'weight' and 'acceleration' features. Split the dataset into a training set and a testing set with the ratio of size 8:2. Train a linear regression model on the training set and evaluate its performance by calculating the mean squared error (MSE) on the testing set.

## Concepts

Machine Learning, Correlation Analysis

## Data Description

Dataset file: `auto-mpg.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
- Use the linear regression algorithm provided by the sklearn library in Python.
- The dataset should be split into a training set and a testing set with the ratio 8:2 using a random_state of 42.
- MSE should be calculated on the testing set only and rounding to two decimal places.
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a CSV with columns `id,answer`, containing one row. In the `answer` cell include:
@test_mse[test_mse]

"test_mse" is the mean squared error of the testing set, rounded to two decimal places.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
