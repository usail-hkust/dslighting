# DABench Task 363 - Train a machine learning model to predict the amount of sunlight (sun column) based on the temperature, humidity, and wind speed columns. Use a simple linear regression model. Split the dataset into a 70-30 training-testing split, and evaluate the model's performance using the mean squared error.

## Task Description

Train a machine learning model to predict the amount of sunlight (sun column) based on the temperature, humidity, and wind speed columns. Use a simple linear regression model. Split the dataset into a 70-30 training-testing split, and evaluate the model's performance using the mean squared error.

## Concepts

Machine Learning

## Data Description

Dataset file: `weather_train.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

{
Use a simple linear regression model for training.
Split the data into training and testing sets in a 70-30 ratio.
Evaluate the model using mean squared error (make sure your mean squared error is not negative).
}

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `363`
- `answer`: `@mean_squared_error[<mse>]` where `<mse>` is the mean squared error rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
