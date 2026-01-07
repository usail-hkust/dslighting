# DABench Task 70 - Perform machine learning by training a linear regression model to predict the wage based on the features exper, looks, union, goodhlth, black, female, married, south, bigcity, smllcity, service, and educ. Use the Root Mean Squared Error (RMSE) for evaluating the model's performance.

## Task Description

Perform machine learning by training a linear regression model to predict the wage based on the features exper, looks, union, goodhlth, black, female, married, south, bigcity, smllcity, service, and educ. Use the Root Mean Squared Error (RMSE) for evaluating the model's performance.

## Concepts

Machine Learning, Summary Statistics

## Data Description

Dataset file: `beauty and the labor market.csv`

The data is available in the `train.csv` file in the public directory.

## Constraints

Perform the machine learning task using the sklearn library's LinearRegression() function. Split the dataset into a 70% training set and a 30% test set. Set the random seed to 42 for reproducibility of the results. Calculate the RMSE on the test set.

## Files

- `train.csv` - The training data
- `sample_submission.csv` - A sample submission file in the correct format

## Submission Format

Submit a single-row CSV with columns `id,answer`.

- `id`: always `70`
- `answer`: `@RMSE[<RMSE_value>]` where `<RMSE_value>` is a number rounded to two decimals.

## Evaluation

Submissions are evaluated on **exact match** with the ground truth answer (with tolerance of 0.01 for floating-point values).

## Goal

Provide the correct answer in the specified format.

## Difficulty Level

Hard
